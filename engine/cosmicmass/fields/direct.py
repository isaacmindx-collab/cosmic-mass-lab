"""Direct-sum solver of the cosmic field (tasks E2.1, E2.2, E2.3, E2.4).

Compendium, section "Cosmic Mass", paragraph "Cosmic Field Law and law of motion":
the field of a source at rest is `E_cal = -G mu_s e_r / r^2`. With `mu_s = m_s + q_s G`
its two coordinates are

    g = -G_N sum_j m_j r_j / |r_j|^3      and      e = -G_N sum_j q_j r_j / |r_j|^3,

where `r_j` points from source j to the field point. Maxwell's field is `E = -s^2 e`,
so one proton gives `E = K e / r^2` (test T0.5).

The second field of moving bodies (E2.2; the approved answer to question 11, decision D41,
derivation in `team/notes/E2.2.md`): to first order in `v/c`, a body moving with velocity `v_j`
adds `B_cal = (1/c^2) v_j x E_cal_j`, that is

    B_g = (1/c^2) sum_j v_j x g_j      and      b = (1/c^2) sum_j v_j x e_j,

so `B = -s^2 b` is the Biot-Savart field with `mu_0 = 4 pi K / c^2`. It is computed only when the
solver is made with `moving=True` (setting `universe.moving_fields`), so that every result made
without it stays the same. Fixed bodies count as at rest. In 2D the second field is the component
out of the plane, `v_x g_y - v_y g_x`.

Scope and labelled assumptions:
- without `moving=True` the second field is the uniform background alone;
- first order in `v/c` (slow bodies): no retardation, no radiation; the velocity-dependent forces
  between two moving bodies do not obey Newton's third law at this order (`team/notes/E2.2.md`);
- in 2D the bodies are points of three-dimensional space that move in a plane, so the
  field still falls as `1/r^2` (T0.1 asks for the 27.3-day month in 2D);
- softening (decision D10) has the Plummer form `r / (r^2 + eps^2)^(3/2)`; D10 gives the
  length, 1e-3 of the smallest initial separation, but not the form.
"""

import numpy as np

from ..constants import SI, Constants
from ..state import State
from .sample import FieldSample

__all__ = ["DirectSum", "smallest_separation", "debye_length", "BACKGROUND_KEYS"]

BACKGROUND_KEYS = ("g", "e", "B_g", "b")  # uniform background fields (setting U5)
_BLOCK = 2_000_000  # largest number of point-source pairs handled at once


def smallest_separation(state: State) -> float:
    """Smallest distance between two alive bodies (infinite for fewer than two)."""
    x = state.x[state.alive]
    if len(x) < 2:
        return float("inf")
    best = np.inf
    for start in range(0, len(x), max(1, _BLOCK // len(x))):
        chunk = x[start : start + max(1, _BLOCK // len(x))]
        dist = np.linalg.norm(chunk[:, None, :] - x[None, :, :], axis=2)
        dist[np.arange(len(chunk)), start + np.arange(len(chunk))] = np.inf  # not a body with itself
        best = min(best, float(dist.min()))
    return best


def debye_length(state: State, constants: Constants, k_b: float) -> float:
    """The screening length of option L8, from the population state (a labelled choice,
    `team/notes/E4.md`): `sqrt(k_B T / (4 pi K sum_i n_i q_i^2))`, the Debye length. `T` is the
    kinetic temperature of the moving alive bodies; the densities come from the box that bounds the
    alive bodies: its volume in 3D, and in 2D (bodies of 3D space moving in a plane, D21) its area
    times the mean spacing `a = sqrt(area / N)`. Infinite (no screening) without temperature, charge
    or extent."""
    alive = state.alive
    moving = alive & ~state.fixed
    n = int(alive.sum())
    if n < 2 or not np.any(moving):
        return np.inf
    kinetic2 = float(np.sum(state.m[moving] * np.sum(state.v[moving] ** 2, axis=1)))
    temperature = kinetic2 / (state.dimension * int(moving.sum()) * k_b)
    extent = np.ptp(state.x[alive], axis=0)
    if state.dimension == 3:
        volume = float(np.prod(extent))
    else:
        area = float(np.prod(extent))
        volume = area * np.sqrt(area / n)
    charge2 = float(np.sum(state.q[alive] ** 2))
    if temperature <= 0 or charge2 == 0 or volume <= 0:
        return np.inf
    return float(np.sqrt(k_b * temperature * volume / (4 * np.pi * constants.K * charge2)))


class DirectSum:
    """`O(P N)` sum over the alive bodies of a state, in NumPy blocks, in 2D and 3D.

    `constants` gives `G_N` (SI or scaled). `softening` is the Plummer length (0 for
    none). `background` maps any of "g", "e", "B_g", "b" to a uniform field.
    """

    def __init__(
        self,
        constants: Constants = SI,
        softening: float = 0.0,
        background: dict | None = None,
        moving: bool = False,
    ):
        self.moving = bool(moving)  # E2.2: the second field of moving bodies (D41)
        if not softening >= 0:
            raise ValueError("the softening length must be zero or positive")
        unknown = sorted(set(background or {}) - set(BACKGROUND_KEYS))
        if unknown:
            raise ValueError(f"unknown background field(s) {unknown}; known: {list(BACKGROUND_KEYS)}")
        self.constants = constants
        self.softening = float(softening)
        self.background = {k: np.asarray(v, dtype=float) for k, v in (background or {}).items()}

    @classmethod
    def with_default_softening(cls, state: State, fraction: float = 1e-3, **kwargs) -> "DirectSum":
        """Softening of decision D10: `fraction` of the smallest initial separation."""
        sep = smallest_separation(state)
        return cls(softening=fraction * sep if np.isfinite(sep) else 0.0, **kwargs)

    # --- the interface of every solver ------------------------------------
    def sample(self, state: State, points: np.ndarray) -> FieldSample:
        """The field of every alive body at arbitrary points, plus the background. A point
        that coincides with a body needs a softening length; use `at_bodies` for the bodies."""
        return self._sample(state, np.asarray(points, dtype=float), skip_self=False)

    def at_bodies(self, state: State) -> FieldSample:
        """The field at every body from all the other alive bodies (no self-field)."""
        return self._sample(state, state.x, skip_self=True)

    def at_bodies_screened(self, state: State, length: float) -> FieldSample:
        """The same, with each body's field screened over `length` (option L8): the kernel
        `1/r^2` becomes `exp(-r/L) (1 + r/L) / r^2`. The uniform background is not screened."""
        return self._sample(state, state.x, skip_self=True, screening=length)

    # --- internals ----------------------------------------------------------
    def _sample(self, state: State, points: np.ndarray, skip_self: bool, screening: float = np.inf) -> FieldSample:
        d = state.dimension
        if points.ndim != 2 or points.shape[1] != d:
            raise ValueError(f"points must have shape (P, {d})")
        src = np.flatnonzero(state.alive)
        xs, ms, qs = state.x[src], state.m[src], state.q[src]
        g, e = np.zeros_like(points), np.zeros_like(points)
        zero = FieldSample.zeros(len(points), d)
        bg, bc = zero.B_g.copy(), zero.b.copy()  # sum_j weight m_j (v_j x r_j), and with q_j
        vs = np.where(state.fixed[src, None], 0.0, state.v[src]) if self.moving else None
        step = max(1, _BLOCK // max(1, len(src)))
        eps2 = self.softening**2
        for start in range(0, len(points) if len(src) else 0, step):
            r = points[start : start + step, None, :] - xs[None, :, :]  # (p, n, d)
            dist2 = np.einsum("pnd,pnd->pn", r, r) + eps2
            if skip_self:  # body i does not act on itself
                rows = start + np.arange(r.shape[0])
                own = rows[:, None] == src[None, :]
                dist2[own] = np.inf
            with np.errstate(divide="ignore", invalid="ignore"):
                weight = dist2**-1.5  # 1 / (r^2 + eps^2)^(3/2)
                if np.isfinite(screening):  # option L8: exp(-r/L) (1 + r/L)
                    ratio = np.sqrt(dist2) / screening
                    weight = np.where(np.isfinite(dist2), weight * np.exp(-ratio) * (1 + ratio), 0.0)
            g[start : start + step] = np.einsum("pn,pnd->pd", weight * ms, r)
            e[start : start + step] = np.einsum("pn,pnd->pd", weight * qs, r)
            if vs is not None:  # E2.2: v_j x r_j for every pair
                if d == 3:
                    turn = np.cross(np.broadcast_to(vs[None, :, :], r.shape), r)  # (p, n, 3)
                    bg[start : start + step] = np.einsum("pn,pnd->pd", weight * ms, turn)
                    bc[start : start + step] = np.einsum("pn,pnd->pd", weight * qs, turn)
                else:
                    turn = vs[None, :, 0] * r[:, :, 1] - vs[None, :, 1] * r[:, :, 0]  # (p, n), out of the plane
                    bg[start : start + step] = np.einsum("pn,pn->p", weight * ms, turn)
                    bc[start : start + step] = np.einsum("pn,pn->p", weight * qs, turn)
        G = self.constants.G_N
        if vs is not None:  # B_cal = (1/c^2) sum_j v_j x E_cal_j, with E_cal_j = -G mu_j r_j / |r_j|^3
            c2 = self.constants.c**2
            field = FieldSample(-G * g, -G * e, -G * bg / c2, -G * bc / c2)
        else:
            field = FieldSample(-G * g, -G * e, zero.B_g, zero.b)
        return field + self._background(len(points), d) if self.background else field

    def _background(self, points: int, d: int) -> FieldSample:
        zero = FieldSample.zeros(points, d)
        parts = {}
        for key in BACKGROUND_KEYS:
            base = getattr(zero, key)
            value = self.background.get(key)
            if value is not None and value.shape != base.shape[1:]:
                raise ValueError(f"background '{key}' must have shape {base.shape[1:]} in {d}D")
            parts[key] = base if value is None else base + value
        return FieldSample(**parts)
