"""The environment of the bodies: walls (task E6a).

A **reflecting** wall turns back the velocity component of a body that has crossed it
and is still moving outwards. The body is not moved, so its position, its speed and
therefore its kinetic and potential energy are exactly what they were: reflecting
walls conserve energy exactly. The momentum given to each wall is reported, for the
pressure on the walls (E8.1).

An **absorbing** wall takes a body that has crossed it out of the motion: the body is
switched off (`alive = False`), never deleted, and its mass, charge and momentum are
added to the collector of the walls (`Environment.collected`). Its row keeps its `m`
and `q`, so the totals of the state still count it: total mass and total charge are
conserved exactly, counting the collector. An absorbed body is no longer a source of
the field, and the energy it carried leaves the bodies.

**Inflow** (setting U7, task E6b): bodies of one cosmic mass enter the box through one
face, at a given rate and velocity. The number that has entered by time `t` is
`floor(rate t)` (deterministic, so the rate is exact to one body); the place on the face
is drawn from the seeded generator. New bodies are appended to the state.

**Heat bath** (task E6b): an Andersen bath. In a step `dt` each moving body is hit with
probability `1 - exp(-nu dt)` (`nu`, the collision rate) and then gets a new velocity
drawn from the Maxwell distribution of the bath temperature for its own mass `Re(mu) = m`.
The temperature of a population is read from its kinetic energy,
`(d/2) N k_B T = sum m v^2 / 2`. `k_B` is exact in SI (1.380649e-23 J/K); in scaled units
it is taken as 1 (a labelled assumption, `team/notes/E6b.md`).

**Fixed sources** (setting U6) are bodies with `fixed = True` (settings: `"fixed": true`):
they never move, and neither walls, inflow nor the heat bath touch them.

Not yet: wrap-around (what the field does across a wrapped boundary is an open
question, `team/QUESTIONS.md`), absorbing surfaces of bodies such as planets (T4.3).
"""

import math

import numpy as np

from .state import State

__all__ = ["Environment", "Inflow", "HeatBath", "K_B", "kinetic_temperature"]

K_B = {"SI": 1.380649e-23, "scaled": 1.0}  # Boltzmann constant: exact in SI (J/K); 1 in scaled units (assumption)


def kinetic_temperature(state: State, k_b: float) -> float:
    """`T = sum m v^2 / (d N k_B)` over the alive bodies that move (0 if there are none)."""
    moving = state.alive & ~state.fixed
    n = int(moving.sum())
    if n == 0:
        return 0.0
    twice_kinetic = float(np.sum(state.m[moving] * np.sum(state.v[moving] ** 2, axis=1)))
    return twice_kinetic / (state.dimension * n * k_b)


class Inflow:
    """Setting U7: bodies of cosmic mass `m + q G` enter the box through the face `(axis, side)`
    at `rate` bodies per unit time, all with `velocity` (which must point into the box), counted
    from the time `t0` (the start of the run)."""

    def __init__(self, m: float, q: float, rate: float, velocity, axis: int, side: str, lower, upper, name: str = "",
                 t0: float = 0.0):
        self.m, self.q, self.name = float(m), float(q), name
        self.rate = float(rate)
        self.velocity = np.asarray(velocity, dtype=float)
        self.lower, self.upper = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
        self.axis, self.side = int(axis), side
        d = self.lower.shape[0]
        if not (math.isfinite(self.rate) and self.rate > 0):
            raise ValueError("the inflow rate must be a positive number")
        if side not in ("lower", "upper") or not 0 <= self.axis < d:
            raise ValueError(f"the inflow face must be an axis 0..{d - 1} and a side 'lower' or 'upper'")
        if self.velocity.shape != (d,):
            raise ValueError(f"the inflow velocity must have {d} components")
        if (self.velocity[self.axis] > 0) != (side == "lower") or self.velocity[self.axis] == 0:
            raise ValueError("the inflow velocity must point into the box through its face")
        self.added, self.t0 = 0, float(t0)

    def apply(self, state: State, rng) -> dict | None:
        """Append the bodies that are due by `state.t`; returns an event, or None."""
        due = math.floor(self.rate * (state.t - self.t0) + 1e-6)  # a sum of steps may fall just short of a whole
        k = due - self.added
        if k <= 0:
            return None
        d = state.dimension
        x = self.lower + rng.random((k, d)) * (self.upper - self.lower)
        x[:, self.axis] = self.lower[self.axis] if self.side == "lower" else self.upper[self.axis]
        state.m = np.append(state.m, np.full(k, self.m))
        state.q = np.append(state.q, np.full(k, self.q))
        state.x = np.vstack([state.x, x])
        state.v = np.vstack([state.v, np.tile(self.velocity, (k, 1))])
        state.fixed = np.append(state.fixed, np.zeros(k, dtype=bool))
        state.alive = np.append(state.alive, np.ones(k, dtype=bool))
        self.added += k
        return {"inflow": {"bodies": k, "m": k * self.m, "q": k * self.q}}


class HeatBath:
    """An Andersen heat bath at `temperature`, with collision rate `collision_rate` per body."""

    def __init__(self, temperature: float, collision_rate: float, k_b: float):
        if not (temperature > 0 and collision_rate > 0 and k_b > 0):
            raise ValueError("the heat bath needs a positive temperature and a positive collision rate")
        self.temperature, self.rate, self.k_b = float(temperature), float(collision_rate), float(k_b)
        self.collisions = 0

    def apply(self, state: State, dt: float, rng) -> dict | None:
        """Re-draw the velocities of the bodies hit in this step; returns an event, or None."""
        draw = rng.random(state.n)
        hit = state.alive & ~state.fixed & (draw < -math.expm1(-self.rate * dt))
        k = int(hit.sum())
        if k == 0:
            return None
        sigma = np.sqrt(self.k_b * self.temperature / state.m[hit])
        state.v[hit] = rng.standard_normal((k, state.dimension)) * sigma[:, None]
        self.collisions += k
        return {"heat_bath": {"bodies": k}}


class Environment:
    """`boundary` is "open", "reflecting" or "absorbing". A box is given by its `lower` and
    `upper` corners, one number per dimension. `collected` holds what absorbing walls took:
    `{"bodies", "m", "q", "momentum"}`."""

    BOUNDARIES = ("open", "reflecting", "absorbing")

    def __init__(self, boundary: str = "open", lower=None, upper=None, inflow: Inflow | None = None,
                 heat_bath: HeatBath | None = None):
        self.inflow, self.heat_bath = inflow, heat_bath
        if boundary not in self.BOUNDARIES:
            raise ValueError(f"boundary must be one of {list(self.BOUNDARIES)}, not {boundary!r}")
        self.boundary = boundary
        self.lower = self.upper = None
        self.collected = {"bodies": 0, "m": 0.0, "q": 0.0, "momentum": None}
        if boundary != "open":
            if lower is None or upper is None:
                raise ValueError(f"a {boundary} box needs its 'lower' and 'upper' corners")
            self.lower, self.upper = np.asarray(lower, dtype=float), np.asarray(upper, dtype=float)
            if self.lower.shape != self.upper.shape or self.lower.ndim != 1 or not np.all(self.lower < self.upper):
                raise ValueError("'lower' and 'upper' must be lists of one length, with lower < upper")

    def apply(self, state: State, dt: float, rng=None) -> list:
        """Apply the walls, then the inflow and the heat bath, to `state`, in place. Returns one
        event per wall that was hit: `{"wall": (axis, side), "bodies": count, "impulse": momentum
        given to the wall along its axis}`; an absorbing wall adds `"absorbed": {"indices", "m", "q",
        "momentum"}`, with the whole momentum of the bodies it took. The inflow adds
        `{"inflow": {"bodies", "m", "q"}}` and the heat bath `{"heat_bath": {"bodies"}}`. The inflow
        and the heat bath need `rng` (a seeded NumPy generator)."""
        events = self._walls(state)
        if (self.inflow is not None or self.heat_bath is not None) and rng is None:
            raise ValueError("the inflow and the heat bath need a seeded random generator")
        if self.inflow is not None and (event := self.inflow.apply(state, rng)) is not None:
            events.append(event)
        if self.heat_bath is not None and (event := self.heat_bath.apply(state, dt, rng)) is not None:
            events.append(event)
        return events

    def _walls(self, state: State) -> list:
        events = []
        if self.boundary == "open":
            return events
        if self.lower.shape[0] != state.dimension:
            raise ValueError(f"the box has {self.lower.shape[0]} dimensions, the state has {state.dimension}")
        moving = state.alive & ~state.fixed
        for axis in range(state.dimension):
            for side, bound, sign in (("lower", self.lower[axis], -1.0), ("upper", self.upper[axis], 1.0)):
                if self.boundary == "absorbing":
                    out = state.alive & ~state.fixed & (sign * (state.x[:, axis] - bound) > 0)  # not yet taken
                    if np.any(out):
                        momentum = np.sum(state.m[out, None] * state.v[out], axis=0)
                        taken = {"indices": [int(i) for i in np.flatnonzero(out)], "m": float(state.m[out].sum()),
                                 "q": float(state.q[out].sum()), "momentum": [float(p) for p in momentum]}
                        state.alive[out] = False
                        self.collected["bodies"] += int(out.sum())
                        self.collected["m"] += taken["m"]
                        self.collected["q"] += taken["q"]
                        previous = self.collected["momentum"]
                        self.collected["momentum"] = momentum if previous is None else previous + momentum
                        events.append({"wall": (axis, side), "bodies": int(out.sum()), "impulse": float(momentum[axis]),
                                       "absorbed": taken})
                    continue
                out = moving & (sign * (state.x[:, axis] - bound) > 0) & (sign * state.v[:, axis] > 0)
                if np.any(out):
                    impulse = float(2.0 * np.sum(state.m[out] * state.v[out, axis]))
                    state.v[out, axis] = -state.v[out, axis]
                    events.append({"wall": (axis, side), "bodies": int(out.sum()), "impulse": impulse})
        return events
