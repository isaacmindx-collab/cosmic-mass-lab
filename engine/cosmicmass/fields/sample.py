"""The cosmic field at a set of points, and the interface of every field solver.

Compendium, section "Cosmic Mass", paragraph "Cosmic Field Law and law of motion":
the fields have General Number values, `E_cal = g + e G` and `B_cal = B_g + b G`.
The Composer set is Maxwell's, with `E = -s^2 e` and `B = -s^2 b`.
"""

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from ..frame import Frame
from ..gnarray import GNArray

__all__ = ["FieldSample", "FieldSolver"]


@dataclass(frozen=True, slots=True)
class FieldSample:
    """The four real fields at P points of a d-dimensional universe.

    `g` and `e` have shape `(P, d)`. `B_g` and `b` have shape `(P, 3)` in 3D and
    `(P,)` in 2D, where the second field points out of the plane.
    """

    g: np.ndarray
    e: np.ndarray
    B_g: np.ndarray
    b: np.ndarray
    # option L8 "screened": the same field with the screened (Yukawa) kernel of the bodies, filled by
    # the step context only for a law that asks for it; None otherwise (E4.4, addition)
    screened: "FieldSample | None" = None

    def __post_init__(self):
        if self.g.ndim != 2 or self.g.shape[1] not in (2, 3) or self.e.shape != self.g.shape:
            raise ValueError("g and e must both have shape (P, 2) or (P, 3)")
        points, d = self.g.shape
        expected = (points, 3) if d == 3 else (points,)
        if self.B_g.shape != expected or self.b.shape != expected:
            raise ValueError(f"B_g and b must have shape {expected} in {d}D")

    @classmethod
    def zeros(cls, points: int, dimension: int) -> "FieldSample":
        second = (points, 3) if dimension == 3 else (points,)
        return cls(np.zeros((points, dimension)), np.zeros((points, dimension)), np.zeros(second), np.zeros(second))

    def E_cal(self, frame: Frame) -> GNArray:
        """The cosmic field `E_cal = g + e G`."""
        return GNArray(self.g, self.e, frame)

    def B_cal(self, frame: Frame) -> GNArray:
        """The second field `B_cal = B_g + b G`."""
        return GNArray(self.B_g, self.b, frame)

    def __add__(self, other: "FieldSample") -> "FieldSample":
        """Superposition: the Cosmic Field Law is linear."""
        return FieldSample(self.g + other.g, self.e + other.e, self.B_g + other.B_g, self.b + other.b)


class FieldSolver(Protocol):
    """Every field solver has this signature (`ARCHITECTURE.md`, section 10)."""

    def sample(self, state, points: np.ndarray) -> FieldSample: ...
