"""The state of the virtual universe: N bodies as a structure of arrays (task E5.1).

Each body carries one number, its cosmic mass `mu = m + q G`, a position and a
velocity. Absorbed bodies are switched off (`alive = False`), never deleted, so
that the totals of mass and charge can always be accounted for.
"""

from dataclasses import dataclass

import numpy as np

from .frame import Frame
from .gnarray import GNArray

__all__ = ["State"]


@dataclass(slots=True)
class State:
    m: np.ndarray  # (N,)  kg
    q: np.ndarray  # (N,)  C
    x: np.ndarray  # (N, d) m
    v: np.ndarray  # (N, d) m/s
    fixed: np.ndarray  # (N,) bool: pinned sources (U6)
    alive: np.ndarray  # (N,) bool: absorbed bodies are switched off, never deleted
    t: float = 0.0
    # optional columns (decision D37): zeros unless given; read only by the code that needs them
    xc: np.ndarray | None = None  # (N, d) Composer position (the reading L1e)
    vc: np.ndarray | None = None  # (N, d) Composer velocity (L1e)
    spin: np.ndarray | None = None  # (N,) in 2D, (N, 3) in 3D: spin angular momentum (L4 "torque")
    radius: np.ndarray | None = None  # (N,) radius of each body; 0 is a point body

    def __post_init__(self):
        self.m, self.q = np.array(self.m, dtype=float), np.array(self.q, dtype=float)
        self.x, self.v = np.array(self.x, dtype=float), np.array(self.v, dtype=float)
        self.fixed, self.alive = np.array(self.fixed, dtype=bool), np.array(self.alive, dtype=bool)
        n = self.m.shape[0] if self.m.ndim == 1 else -1
        if n < 0 or any(a.shape != (n,) for a in (self.q, self.fixed, self.alive)):
            raise ValueError("m, q, fixed and alive must be one-dimensional arrays of one length N")
        if self.x.ndim != 2 or self.x.shape != self.v.shape or self.x.shape[0] != n:
            raise ValueError("x and v must both have shape (N, d)")
        if self.x.shape[1] not in (2, 3):
            raise ValueError("the dimension d must be 2 or 3")
        if not np.all(np.isfinite(self.m)) or not np.all(np.isfinite(self.q)):
            raise ValueError("m and q must be finite")
        d = self.x.shape[1]
        shapes = {"xc": (n, d), "vc": (n, d), "spin": (n, 3) if d == 3 else (n,), "radius": (n,)}
        for name, shape in shapes.items():
            value = getattr(self, name)
            value = np.zeros(shape) if value is None else np.array(value, dtype=float)
            if value.shape != shape:
                raise ValueError(f"{name} must have shape {shape}")
            setattr(self, name, value)
        if np.any(self.radius < 0):
            raise ValueError("a radius cannot be negative")

    @classmethod
    def from_bodies(cls, bodies, x, v=None, fixed=None, t: float = 0.0) -> "State":
        """A state from a sequence of `CosmicMass` and their positions (velocities default to rest)."""
        x = np.array(x, dtype=float)
        n = len(bodies)
        return cls(
            m=[b.m for b in bodies],
            q=[b.q for b in bodies],
            x=x,
            v=np.zeros_like(x) if v is None else v,
            fixed=np.zeros(n, dtype=bool) if fixed is None else fixed,
            alive=np.ones(n, dtype=bool),
            t=t,
        )

    @property
    def n(self) -> int:
        """Number of bodies, alive or not."""
        return self.m.shape[0]

    @property
    def dimension(self) -> int:
        return self.x.shape[1]

    def mu(self, frame: Frame) -> GNArray:
        """The cosmic masses `mu = m + q G` of all bodies, as General Numbers of `frame`."""
        return GNArray(self.m, self.q, frame)

    def total_mu(self, frame: Frame, alive_only: bool = False) -> GNArray:
        """Total cosmic mass: total mass in `Re`, total charge in `Com`. By default it
        counts every body, absorbed ones included, so absorption never changes it."""
        keep = self.alive if alive_only else np.ones(self.n, dtype=bool)
        return GNArray(self.m[keep].sum(), self.q[keep].sum(), frame)

    def copy(self) -> "State":
        """An independent copy: changing it never changes the original."""
        return State(
            self.m.copy(),
            self.q.copy(),
            self.x.copy(),
            self.v.copy(),
            self.fixed.copy(),
            self.alive.copy(),
            self.t,
            xc=self.xc.copy(),
            vc=self.vc.copy(),
            spin=self.spin.copy(),
            radius=self.radius.copy(),
        )

    def extend(self, m, q, x, v) -> None:
        """Append bodies in place (an inflow): alive, free, with zero optional columns."""
        m, q = np.atleast_1d(np.asarray(m, dtype=float)), np.atleast_1d(np.asarray(q, dtype=float))
        x, v = np.atleast_2d(np.asarray(x, dtype=float)), np.atleast_2d(np.asarray(v, dtype=float))
        k, d = len(m), self.dimension
        if q.shape != (k,) or x.shape != (k, d) or v.shape != (k, d):
            raise ValueError(f"extend: m and q need one length k, x and v the shape (k, {d})")
        self.m, self.q = np.append(self.m, m), np.append(self.q, q)
        self.x, self.v = np.vstack([self.x, x]), np.vstack([self.v, v])
        self.fixed = np.append(self.fixed, np.zeros(k, dtype=bool))
        self.alive = np.append(self.alive, np.ones(k, dtype=bool))
        self.xc, self.vc = np.vstack([self.xc, np.zeros((k, d))]), np.vstack([self.vc, np.zeros((k, d))])
        self.spin = np.vstack([self.spin, np.zeros((k, 3))]) if d == 3 else np.append(self.spin, np.zeros(k))
        self.radius = np.append(self.radius, np.zeros(k))
