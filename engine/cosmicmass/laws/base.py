"""The law interface (task E4.1).

A law turns a state and the cosmic field into forces. The reference law is L0,
the paper's law (decision D1); every other reading, L1 to L8, is a hypothesis
and is labelled as one. A `LawSpec` holds the reading (L0, L1a to L1e) and every
option L2 to L8 of `docs/05-scenarios-and-tests.md`, section 1; it is written
into `stamp.json` in the form of `team/RESULTS-STANDARD.md`, section 2.
"""

from dataclasses import dataclass, fields
from typing import ClassVar

import numpy as np

from .. import readings
from ..fields.sample import FieldSample
from ..frame import Frame
from ..state import State

__all__ = ["LawSpec", "ForcePair", "Law", "register", "make_law", "available_laws", "third_law_residual"]

# field of LawSpec -> (key in stamp.json, allowed values; None means "a number")
_OPTIONS = {
    "reading": ("id", ("L0", "L1a", "L1b", "L1c", "L1d", "L1e")),
    "sign": ("sign", ("+", "-")),  # L2
    "strength": ("lambda", None),  # L3: a number, or "cos_phi_bar"
    "direction": ("direction", ("radial", "perpendicular", "torque", "velocity")),  # L4
    "terms": ("terms", ("all", "s q g", "-m E/s", "-2 cos q E")),  # L5 (all, a, b, c)
    "moving": ("B_cal", ("off", "on", "only")),  # L6
    "inertia": ("inertia", ("Re", "Sh", "abs")),  # L7
    "range": ("range", ("1/r^2", "screened")),  # L8
}


@dataclass(frozen=True, slots=True)
class LawSpec:
    """The reading and every option L2 to L8. The defaults are the default exploratory
    law of `docs/05`, section 1, except the reading, which defaults to the reference L0."""

    reading: str = "L0"
    sign: str = "+"
    strength: float | str = 1.0
    direction: str = "radial"
    terms: str = "all"
    moving: str = "off"
    inertia: str = "Re"
    range: str = "1/r^2"

    def __post_init__(self):
        for name, (key, allowed) in _OPTIONS.items():
            value = getattr(self, name)
            if allowed is not None and value not in allowed:
                raise ValueError(f"law option '{key}' must be one of {list(allowed)}, not {value!r}")
        lam = self.strength
        if lam != "cos_phi_bar" and (isinstance(lam, (bool, str)) or not np.isfinite(lam)):
            raise ValueError(f"law option 'lambda' must be a finite number or 'cos_phi_bar', not {lam!r}")

    def to_dict(self) -> dict:
        """The `law` block of `stamp.json`."""
        return {key: getattr(self, name) for name, (key, _) in _OPTIONS.items()}

    @classmethod
    def from_dict(cls, data: dict) -> "LawSpec":
        """Read a `law` block. Missing options take their defaults; unknown ones are refused."""
        names = {key: name for name, (key, _) in _OPTIONS.items()}
        unknown = sorted(set(data) - set(names))
        if unknown:
            raise ValueError(f"unknown law option(s) {unknown}; known: {sorted(names)}")
        return cls(**{names[key]: value for key, value in data.items()})

    def is_default_except_reading(self) -> bool:
        return all(getattr(self, f.name) == f.default for f in fields(self) if f.name != "reading")


@dataclass(frozen=True, slots=True)
class ForcePair:
    """The forces on the N bodies, shape `(N, d)` each. `real` comes from the Real
    coordinate of `mu (E_cal + v x B_cal)`; `composer` is the force that the law reads
    from the Composer coordinate (zero under L0). The force applied is their sum."""

    real: np.ndarray
    composer: np.ndarray

    def total(self) -> np.ndarray:
        return self.real + self.composer


class Law:
    """Base class of every law. A subclass sets `reading` and implements `forces`."""

    reading: ClassVar[str] = ""
    hypothesis: ClassVar[bool] = True  # only L0 is not a hypothesis (decision D1)

    def __init__(self, spec: LawSpec | None = None):
        self.spec = LawSpec(reading=self.reading) if spec is None else spec
        if self.spec.reading != self.reading:
            raise ValueError(f"a {self.reading} law cannot take a spec for {self.spec.reading}")

    @property
    def id(self) -> str:
        return self.spec.reading

    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair:
        raise NotImplementedError

    def inertia(self, state: State, frame: Frame) -> np.ndarray:
        """The inertia of each body, a reading of its cosmic mass (option L7; tasks E3.4, E4.4):
        `Re(mu) = m` (the default, and L0's), `Sh(mu) = m + q s cos(phi_bar)` or
        `abs(mu) = sqrt(Sh^2 + Ht^2)`. `Sh(mu)` can be zero or negative (for an electron it is
        negative): a hypothesis to explore (T8); a zero inertia is refused by the integrator."""
        mu = state.mu(frame)
        if self.spec.inertia == "Re":
            return mu.re
        if self.spec.inertia == "Sh":
            return readings.Sh(mu)
        return readings.abs(mu)

    def velocity_coupling(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """The vector `W` such that the velocity-dependent part of the force is `v x W` (used by the
        Boris push). L0's: `m B_g + q B = m B_g - s^2 q b`, the Real coordinate of `mu B_cal`.
        Shape `(N,)` in 2D (out of the plane), `(N, 3)` in 3D."""
        if fields.B_g.ndim == 2:
            return state.m[:, None] * fields.B_g - frame.s**2 * state.q[:, None] * fields.b
        return state.m * fields.B_g - frame.s**2 * state.q * fields.b

    def composer_acceleration(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray | None:
        """The acceleration of the Composer coordinate of each body's position, shape `(N, d)`, for a
        law in which bodies move in two coordinates (L1e); `None` for every other law (D37)."""
        return None

    def torque(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray | None:
        """The torque on each body's spin (option L4 "torque"), shape `(N,)` in 2D, `(N, 3)` in 3D;
        `None` when the law gives none (D37)."""
        return None


_REGISTRY: dict[str, type[Law]] = {}


def register(law_class: type[Law]) -> type[Law]:
    """Class decorator: add a law to the registry under its reading."""
    if law_class.reading in _REGISTRY:
        raise ValueError(f"law {law_class.reading} is already registered")
    _REGISTRY[law_class.reading] = law_class
    return law_class


def available_laws() -> list[str]:
    return sorted(_REGISTRY)


def make_law(spec: LawSpec | str) -> Law:
    """Build a law from a spec or from a reading name such as "L0"."""
    spec = LawSpec(reading=spec) if isinstance(spec, str) else spec
    if spec.reading not in _REGISTRY:
        raise NotImplementedError(f"law {spec.reading} is not implemented; available: {available_laws()}")
    return _REGISTRY[spec.reading](spec)


def third_law_residual(law: Law, state: State, solver, frame: Frame) -> dict:
    """Newton's third law check (task E4.5, used by T1.6). For every pair of alive bodies, the
    force on a from b alone and the force on b from a alone are computed with `solver` (which must
    have no background field) and `law`, and added. Returns the pair with the largest
    `|F_ab + F_ba| / max(|F_ab|, |F_ba|)`: `{"pair", "residual", "force", "relative"}`; the relative
    residual is 0 when the law obeys the third law, and `None` when no pair exerts any force."""
    worst = {"pair": None, "residual": 0.0, "force": 0.0, "relative": None}
    alive = np.flatnonzero(state.alive)
    for position, i in enumerate(alive):
        for j in alive[position + 1 :]:
            pick = [i, j]
            pair = State(
                state.m[pick], state.q[pick], state.x[pick], state.v[pick], [False, False], [True, True], state.t
            )
            force = law.forces(pair, solver.at_bodies(pair), frame).total()
            size = float(max(np.linalg.norm(force[0]), np.linalg.norm(force[1])))
            if size == 0.0:
                continue
            residual = float(np.linalg.norm(force[0] + force[1]))
            if worst["relative"] is None or residual / size > worst["relative"]:
                worst = {"pair": (int(i), int(j)), "residual": residual, "force": size, "relative": residual / size}
    return worst
