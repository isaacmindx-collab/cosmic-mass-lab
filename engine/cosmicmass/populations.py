"""Seeded population generators (task E5.4; setting U8, "population state: number density per mu
type, velocity spread (temperature) per type, bulk flow").

A population is many bodies of one cosmic mass, placed by a shape and moving with a velocity rule:

- shapes: `box` (uniform in a box), `shell` (uniform in a spherical shell; an annulus in 2D),
  `ring` (uniform in an annulus of the plane z = 0; in 2D the same as `shell`);
- velocities: a bulk flow, plus a **thermal spread** at a temperature (each component normal with
  variance `k_B T / m`, the Maxwell distribution of the inertia `Re(mu) = m`), plus an optional
  **Keplerian** circular speed `sqrt(G_N M / r)` about a centre of mass `M` (turning counter-clockwise
  in the plane);
- **super-particles:** a `weight` multiplies the mass and the charge of each body, so that one body
  stands for `weight` real ones with the same charge-to-mass ratio, and so the same acceleration in
  the same field.

Labelled choices (`team/notes/E5.md`): the thermal spread of a super-particle uses the mass of the
**real** particle it stands for (so a super-particle of protons at 1e4 K moves like a proton at
1e4 K); every draw comes from one generator seeded from `numerics.seed` (D13), in the order the
populations are listed, so the same settings give the same bodies.
"""

import numpy as np

from .environment import K_B

__all__ = ["generate", "SHAPES", "POPULATION_KEYS"]

SHAPES = ("box", "shell", "ring")
POPULATION_KEYS = {
    "preset",
    "name",
    "m",
    "q",
    "n",
    "shape",
    "lower",
    "upper",
    "centre",
    "radius",
    "width",
    "temperature",
    "bulk",
    "keplerian",
    "weight",
}


def _unit_vectors(n: int, d: int, rng) -> np.ndarray:
    u = rng.standard_normal((n, d))
    return u / np.linalg.norm(u, axis=1)[:, None]


def _radii(n: int, r_in: float, r_out: float, power: int, rng) -> np.ndarray:
    """Radii uniform in area (power 2) or volume (power 3) between r_in and r_out."""
    u = rng.random(n)
    return (r_in**power + u * (r_out**power - r_in**power)) ** (1.0 / power)


def positions(spec: dict, d: int, rng) -> np.ndarray:
    """The positions of a population, shape `(n, d)`."""
    n, shape = spec["n"], spec["shape"]
    if shape == "box":
        lower, upper = np.asarray(spec["lower"], float), np.asarray(spec["upper"], float)
        return lower + rng.random((n, d)) * (upper - lower)
    centre = np.asarray(spec.get("centre", [0.0] * d), float)
    radius, width = float(spec["radius"]), float(spec.get("width", 0.0))
    r_in, r_out = radius - width / 2, radius + width / 2
    if shape == "shell" and d == 3:
        return centre + _radii(n, r_in, r_out, 3, rng)[:, None] * _unit_vectors(n, 3, rng)
    # an annulus of the plane (2D shell, and the ring in 2D or 3D)
    angle = rng.random(n) * 2 * np.pi
    r = _radii(n, r_in, r_out, 2, rng)
    out = np.zeros((n, d))
    out[:, 0], out[:, 1] = r * np.cos(angle), r * np.sin(angle)
    return centre + out


def velocities(spec: dict, x: np.ndarray, real_mass: float, constants, rng) -> np.ndarray:
    """Bulk flow + thermal spread at the population's temperature + Keplerian circular speed."""
    n, d = x.shape
    v = np.tile(np.asarray(spec.get("bulk", [0.0] * d), float), (n, 1))
    temperature = float(spec.get("temperature", 0.0))
    if temperature > 0:
        sigma = np.sqrt(K_B[constants.units] * temperature / real_mass)
        v += sigma * rng.standard_normal((n, d))
    kepler = spec.get("keplerian")
    if kepler is not None:
        centre = np.asarray(kepler.get("centre", spec.get("centre", [0.0] * d)), float)
        rel = x - centre
        r = np.hypot(rel[:, 0], rel[:, 1])
        off = r > 0  # a body on the axis has no circular direction: it gets no Keplerian speed
        speed = np.zeros(n)
        speed[off] = np.sqrt(constants.G_N * float(kepler["mass"]) / r[off])
        safe = np.where(off, r, 1.0)
        v[:, 0] += -speed * rel[:, 1] / safe  # counter-clockwise in the plane
        v[:, 1] += speed * rel[:, 0] / safe
    return v


def generate(spec: dict, d: int, constants, rng, real: tuple) -> dict:
    """One population as arrays: `m`, `q` (weighted), `x`, `v` and its `name`. `real` is the cosmic
    mass `(m, q)` of the real particle it is made of."""
    weight = float(spec.get("weight", 1.0))
    m, q = real
    x = positions(spec, d, rng)
    v = velocities(spec, x, m, constants, rng)
    n = spec["n"]
    return {"m": np.full(n, m * weight), "q": np.full(n, q * weight), "x": x, "v": v}
