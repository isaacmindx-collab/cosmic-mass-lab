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
"""

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .frame import Frame
from .laws.base import Law
from .state import State

__all__ = ["StepContext", "Integrator", "VelocityVerlet", "nearest_distances", "nearest_neighbours", "REST_FRACTION"]

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
    # whose motion the step rule looks at: "absolute" (each body's own velocity and acceleration:
    # D10 and D21) or "neighbour" (relative to its nearest neighbour; tested in scenario Q4, not a default)
    speed_reference: str = "absolute"
    _cache: tuple | None = field(default=None, repr=False)

    def acceleration(self, state: State) -> np.ndarray:
        """`force / inertia` for every moving body; zero for fixed and absorbed bodies."""
        if self._cache is not None and self._cache[0] is state:
            return self._cache[1]
        force = self.law.forces(state, self.solver.at_bodies(state), self.frame).total()
        inertia = self.law.inertia(state, self.frame)
        moving = state.alive & ~state.fixed
        if np.any(inertia[moving] == 0):
            raise ZeroDivisionError("a moving body has zero inertia under this law; the motion is undefined")
        a = np.zeros_like(force)
        a[moving] = force[moving] / inertia[moving, None]
        self._cache = (state, a)
        return a

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
        dt = min(max(dt, ctx.dt_min), ctx.dt_max)
        if not np.isfinite(dt) or dt <= 0:
            raise ValueError("no time step can be derived from the motion; give numerics.dt_max")
        return dt

    def step(self, state: State, dt: float, ctx: StepContext) -> State:
        a0 = ctx.acceleration(state)
        new = state.copy()
        moving = state.alive & ~state.fixed
        v_half = state.v + (0.5 * dt) * a0
        new.x[moving] = state.x[moving] + dt * v_half[moving]
        new.v[moving] = v_half[moving]
        new.t = state.t + dt
        ctx.invalidate()
        a1 = ctx.acceleration(new)  # computed with the half-step velocity, then remembered
        new.v[moving] = v_half[moving] + (0.5 * dt) * a1[moving]
        return new
