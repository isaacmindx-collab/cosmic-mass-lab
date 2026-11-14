"""Integrators of the law of motion (tasks E3.1 and E3.3; decision D10).

Velocity Verlet advances `inertia dv/dt = force`, with the force and the inertia
given by a `Law` and the field by a `FieldSolver`. For the reference law L0
(compendium, "Cosmic Field Law and law of motion") this is
`Re(mu) dv/dt = Re[mu (E_cal + v x B_cal)]`.

Scope and labelled assumptions:
- velocity Verlet is exact in its symmetry only for forces that do not depend on the
  velocity. The `v x B_cal` term needs the Boris push (E3.2), outside the MVP;
- adaptive step (D10): "the largest velocity change per step is below 1e-3 of the
  speed", so `dt = eta |v| / |a|`, smallest over the bodies. Two additions, both
  assumptions:
  1. a body at rest has no speed, and the rule would give a zero step. Its speed is
     taken as at least `REST_FRACTION sqrt(|a| l)`, a tenth of the free-fall speed over
     the distance `l` to its nearest neighbour. D10 holds as written for every body
     faster than that. A body with no neighbour at all (alone in a background field)
     has no such floor, and D10's rule would make it creep towards every turning point
     without ever passing it; such a body does not limit the step, which is then
     `dt_max`. In a uniform field velocity Verlet is exact at any step;
  2. no body moves more than `eta` of the distance to its nearest neighbour in one
     step. This only ever shortens the step. Without it the step of two bodies flying
     apart grows without limit.
- decision D29 (amending D21, convention 4; scenarios Q4 and Q5): by default the conditions
  above are taken **relative to each body's nearest neighbour** (`speed_reference =
  "neighbour"`), so the step does not depend on the frame; and the **pair guard**
  `dt <= eta min_(i<j) r_ij / |v_i - v_j|` over every pair of alive bodies is always applied,
  so that a fast passage that no body's nearest neighbour sees still gets short steps. The
  guard only ever shortens a step. `speed_reference = "absolute"` keeps the rule of D10 and
  D21 (each body's own motion), plus the guard.
"""

from dataclasses import dataclass, field, replace
from typing import Protocol

import numpy as np

from .environment import K_B
from .fields.direct import debye_length
from .frame import Frame
from .laws.base import Law
from .state import State

__all__ = [
    "StepContext",
    "Integrator",
    "VelocityVerlet",
    "Boris",
    "boris_rotation",
    "advance_secondary",
    "nearest_distances",
    "nearest_neighbours",
    "pair_approach_time",
    "REST_FRACTION",
]

REST_FRACTION = 0.1  # floor of the speed in the adaptive step, as a fraction of sqrt(|a| l)


def nearest_distances(state: State) -> np.ndarray:
    """Distance from each body to the nearest other alive body (infinite if there is none)."""
    return nearest_neighbours(state)[0]


def nearest_neighbours(state: State) -> tuple:
    """For each body, the distance to the nearest other alive body (infinite if there is none)
    and the index of that body (the body's own index if there is none)."""
    out = np.full(state.n, np.inf)
    partner = np.arange(state.n)
    idx = np.flatnonzero(state.alive)
    if len(idx) > 1:
        x = state.x[idx]
        step = max(1, 2_000_000 // len(idx))
        for start in range(0, len(idx), step):
            diff = x[start : start + step, None, :] - x[None, :, :]
            dist = np.sqrt(np.einsum("pnd,pnd->pn", diff, diff))
            rows = np.arange(dist.shape[0])
            dist[rows, start + rows] = np.inf
            out[idx[start : start + step]] = dist.min(axis=1)
            partner[idx[start : start + step]] = idx[dist.argmin(axis=1)]
    return out, partner


def pair_approach_time(state: State) -> float:
    """`min_(i<j) r_ij / |v_i - v_j|` over the pairs of alive bodies that move relative to each
    other (infinite if none does). Fixed bodies count as at rest. The pair guard of D29 is
    `eta` times this time."""
    idx = np.flatnonzero(state.alive)
    if len(idx) < 2:
        return np.inf
    x = state.x[idx]
    v = np.where(state.fixed[idx, None], 0.0, state.v[idx])
    best = np.inf
    step = max(1, 2_000_000 // len(idx))
    for start in range(0, len(idx), step):
        dx = x[start : start + step, None, :] - x[None, :, :]
        dv = v[start : start + step, None, :] - v[None, :, :]
        r = np.sqrt(np.einsum("pnd,pnd->pn", dx, dx))
        w = np.sqrt(np.einsum("pnd,pnd->pn", dv, dv))
        moving = w > 0  # a body with itself, and pairs at rest relative to each other, are left out
        if np.any(moving):
            best = min(best, float(np.min(r[moving] / w[moving])))
    return best


@dataclass
class StepContext:
    """What a step needs besides the state: the law, the field solver, the frame and
    the numerics of the adaptive step. It remembers the last acceleration it computed,
    so that a step does not evaluate the field twice at the same positions."""

    law: Law
    solver: object  # a FieldSolver that also has at_bodies(state)
    frame: Frame
    eta: float = 1e-3  # D10: largest velocity change per step, as a fraction of the speed
    dt_min: float = 0.0
    dt_max: float = np.inf
    # whose motion the step rule looks at: "neighbour" (relative to its nearest neighbour: the
    # default since D29) or "absolute" (each body's own velocity and acceleration: D10 and D21)
    speed_reference: str = "neighbour"
    _cache: tuple | None = field(default=None, repr=False)

    def acceleration(self, state: State) -> np.ndarray:
        """`force / inertia` for every moving body; zero for fixed and absorbed bodies."""
        if self._cache is not None and self._cache[0] is state:
            return self._cache[1]
        fields = self.solver.at_bodies(state)
        if getattr(self.law.spec, "range", "1/r^2") == "screened":  # option L8: the screened field too
            length = debye_length(state, self.solver.constants, K_B[self.solver.constants.units])
            fields = replace(fields, screened=self.solver.at_bodies_screened(state, length))
        force = self.law.forces(state, fields, self.frame).total()
        inertia = self.law.inertia(state, self.frame)
        moving = state.alive & ~state.fixed
        if np.any(inertia[moving] == 0):
            raise ZeroDivisionError("a moving body has zero inertia under this law; the motion is undefined")
        a = np.zeros_like(force)
        a[moving] = force[moving] / inertia[moving, None]
        self._cache = (state, a, fields, inertia)
        return a

    def rotation(self, state: State) -> np.ndarray:
        """The rotation rate `Omega` of each moving body, such that the velocity-dependent part of its
        acceleration is `v x Omega`: `Omega = (m B_g + q B) / inertia`, with `B = -s^2 b` (the Real
        coordinate of `mu (v x B_cal)`, L0). Shape `(N,)` in 2D (out of the plane), `(N, 3)` in 3D;
        zero for fixed and absorbed bodies."""
        self.acceleration(state)
        _, _, fields, inertia = self._cache
        moving = state.alive & ~state.fixed
        per_body = np.where(moving, 1.0 / np.where(moving, inertia, 1.0), 0.0)  # 1 / inertia, 0 if not moving
        coupling = self.law.velocity_coupling(state, fields, self.frame)  # L0's: m B_g - s^2 q b
        return coupling * (per_body[:, None] if coupling.ndim == 2 else per_body)

    def secondary(self, state: State) -> tuple:
        """`(composer_acceleration, torque)` of the law at `state` (each `None` if the law gives none),
        with the fields remembered for this state and its present velocity (decision D37)."""
        self.acceleration(state)
        fields = self._cache[2]
        return (
            self.law.composer_acceleration(state, fields, self.frame),
            self.law.torque(state, fields, self.frame),
        )

    def remember(self, state: State, a: np.ndarray) -> None:
        """Replace the remembered acceleration of `state` (the same positions, so the same fields),
        after its velocity changed: used by the Boris push, whose force is linear in the velocity."""
        if self._cache is None or self._cache[0] is not state:
            raise ValueError("remember() needs the acceleration of this state computed first")
        self._cache = (state, a, *self._cache[2:])

    def invalidate(self) -> None:
        """Forget the remembered acceleration (after anything else changed the state)."""
        self._cache = None


class Integrator(Protocol):
    def next_dt(self, state: State, ctx: StepContext) -> float: ...
    def step(self, state: State, dt: float, ctx: StepContext) -> State: ...


class VelocityVerlet:
    """Half kick, drift, new field, half kick. Second order, time-reversible at a fixed step."""

    def next_dt(self, state: State, ctx: StepContext) -> float:
        moving = state.alive & ~state.fixed
        acceleration, velocity = ctx.acceleration(state), state.v
        reach, partner = nearest_neighbours(state)
        near = np.isfinite(reach)
        if ctx.speed_reference == "neighbour":  # motion relative to the nearest neighbour (a fixed body is at rest)
            velocity = np.where(moving[:, None], state.v, 0.0)
            acceleration, velocity = acceleration - acceleration[partner], velocity - velocity[partner]
        elif ctx.speed_reference != "absolute":
            raise ValueError(f"speed_reference must be 'absolute' or 'neighbour', not {ctx.speed_reference!r}")
        a = np.linalg.norm(acceleration, axis=1)
        speed = np.linalg.norm(velocity, axis=1)
        dt = np.inf
        # D10: |a| dt <= eta |v|, with the floor of the speed for bodies at rest;
        # a body with no neighbour does not limit the step
        floor = np.where(near, REST_FRACTION * np.sqrt(a * np.where(near, reach, 0.0)), 0.0)
        scale = np.maximum(speed, floor)
        pushed = moving & near & (a > 0) & (scale > 0)
        if np.any(pushed):
            dt = float(np.min(ctx.eta * scale[pushed] / a[pushed]))
        # no body moves more than eta of the distance to its nearest neighbour
        crossing = moving & (speed > 0) & near
        if np.any(crossing):
            dt = min(dt, float(np.min(ctx.eta * reach[crossing] / speed[crossing])))
        # D29: the pair guard, for passages that no body's nearest neighbour sees
        dt = min(dt, ctx.eta * pair_approach_time(state))
        dt = min(max(dt, ctx.dt_min), ctx.dt_max)
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("no time step can be derived from the motion; give numerics.dt_max")
        return dt

    def step(self, state: State, dt: float, ctx: StepContext) -> State:
        a0 = ctx.acceleration(state)
        before = ctx.secondary(state)
        new = state.copy()
        moving = state.alive & ~state.fixed
        v_half = state.v + (0.5 * dt) * a0
        new.x[moving] = state.x[moving] + dt * v_half[moving]
        new.v[moving] = v_half[moving]
        new.t = state.t + dt
        ctx.invalidate()
        a1 = ctx.acceleration(new)  # computed with the half-step velocity, then remembered
        new.v[moving] = v_half[moving] + (0.5 * dt) * a1[moving]
        advance_secondary(state, new, dt, before, ctx.secondary(new))
        return new


def advance_secondary(state: State, new: State, dt: float, before: tuple, after: tuple) -> None:
    """Advance the optional columns of D37 over one step, in `new`, with the same scheme as the Real
    coordinate (half kick, drift, half kick): the Composer position `xc` moves with the Composer
    velocity `vc`, which is kicked by the law's Composer acceleration (L1e); the spin is turned by the
    law's torque (L4 "torque"). Fixed and absorbed bodies are left alone. With no Composer velocity,
    acceleration or torque, nothing is touched."""
    (ac0, tq0), (ac1, tq1) = before, after
    moving = state.alive & ~state.fixed
    h = 0.5 * dt
    if ac0 is not None or state.vc.any():
        vc_half = state.vc if ac0 is None else state.vc + h * ac0
        new.xc[moving] = state.xc[moving] + dt * vc_half[moving]
        new.vc[moving] = vc_half[moving] if ac1 is None else vc_half[moving] + h * ac1[moving]
    if tq0 is not None and tq1 is not None:
        new.spin[moving] = state.spin[moving] + h * (tq0[moving] + tq1[moving])


def _cross(v: np.ndarray, omega: np.ndarray) -> np.ndarray:
    """`v x Omega` for N bodies: `Omega` of shape `(N, 3)` in 3D, `(N,)` out of the plane in 2D."""
    if v.shape[1] == 3:
        return np.cross(v, omega)
    return np.stack([v[:, 1] * omega, -v[:, 0] * omega], axis=1)


def boris_rotation(v: np.ndarray, omega: np.ndarray, h: float) -> np.ndarray:
    """Turn `v` as `dv/dt = v x Omega` does over a time `h`, with Boris's formula: the speed is kept
    exactly, and the angle is `2 atan(|Omega| h / 2)` instead of `|Omega| h` (an error of
    `(|Omega| h)^3 / 12` per call)."""
    t = omega * (0.5 * h)
    t2 = np.sum(t * t, axis=1) if t.ndim == 2 else t * t
    s = 2.0 * t / (1.0 + (t2[:, None] if t.ndim == 2 else t2))
    v_prime = v + _cross(v, t)
    return v + _cross(v_prime, s)


class Boris(VelocityVerlet):
    """Velocity Verlet with the Boris push for `v x B_cal` (task E3.2; D10: "Boris with `B_cal`").

    The acceleration is split as `a = a_E(x) + v x Omega(x)` (`StepContext.rotation`). One step is
    velocity Verlet in which each half kick is a Boris push over half the step (a quarter kick with
    `a_E`, a turn with `Omega`, a quarter kick): push at `x_n`, drift, push at `x_(n+1)`. It is second
    order and time-reversible; the turns keep the speed exactly; a charge moving at the drift velocity
    `E x B / B^2` in uniform fields stays on it exactly (the Boris push keeps that drift at any step);
    with no second field (`Omega = 0`) it is velocity Verlet. The same adaptive step (`next_dt`).

    Scope: the velocity-dependent force is the Real coordinate of `mu (v x B_cal)` (L0's), which is
    the only one every implemented law reads; a law that reads the Composer coordinate of
    `mu (v x B_cal)` (option L6, `B_cal` on) is refused."""

    def step(self, state: State, dt: float, ctx: StepContext) -> State:
        if getattr(ctx.law.spec, "moving", "off") != "off":
            raise NotImplementedError("the Boris push reads only the Real coordinate of mu (v x B_cal) (L6 off)")
        h = 0.5 * dt
        moving = state.alive & ~state.fixed
        a0, omega0 = ctx.acceleration(state), ctx.rotation(state)
        before = ctx.secondary(state)
        v = self._push(state.v, a0 - _cross(state.v, omega0), omega0, h)  # half step at x_n
        new = state.copy()
        new.x[moving] = state.x[moving] + dt * v[moving]  # drift
        new.v[moving] = v[moving]
        new.t = state.t + dt
        ctx.invalidate()
        a1, omega1 = ctx.acceleration(new), ctx.rotation(new)  # at the new place, with the half-step velocity
        a_e1 = a1 - _cross(new.v, omega1)
        v = self._push(new.v, a_e1, omega1, h)  # half step at x_(n+1)
        new.v[moving] = v[moving]
        ctx.remember(new, a_e1 + _cross(new.v, omega1))  # the acceleration at the final velocity
        advance_secondary(state, new, dt, before, ctx.secondary(new))
        return new

    @staticmethod
    def _push(v: np.ndarray, a_e: np.ndarray, omega: np.ndarray, h: float) -> np.ndarray:
        """The Boris push over a time `h`: quarter kick, turn, quarter kick (with `h/2` kicks)."""
        v = v + (0.5 * h) * a_e
        v = boris_rotation(v, omega, h)
        return v + (0.5 * h) * a_e
