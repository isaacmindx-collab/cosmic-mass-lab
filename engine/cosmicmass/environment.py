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

Not yet: wrap-around (what the field does across a wrapped boundary is an open
question, `team/QUESTIONS.md`), absorbing surfaces of bodies such as planets (T4.3),
inflow and the heat bath (E6b).
"""

import numpy as np

from .state import State

__all__ = ["Environment"]


class Environment:
    """`boundary` is "open", "reflecting" or "absorbing". A box is given by its `lower` and
    `upper` corners, one number per dimension. `collected` holds what absorbing walls took:
    `{"bodies", "m", "q", "momentum"}`."""

    BOUNDARIES = ("open", "reflecting", "absorbing")

    def __init__(self, boundary: str = "open", lower=None, upper=None):
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
        """Apply the walls to `state`, in place. Returns one event per wall that was hit:
        `{"wall": (axis, side), "bodies": count, "impulse": momentum given to the wall along its
        axis}`; an absorbing wall adds `"absorbed": {"indices", "m", "q", "momentum"}`, with the
        whole momentum of the bodies it took."""
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
