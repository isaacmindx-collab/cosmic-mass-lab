"""Diagnostics (task E8.1): total cosmic mass (mass and charge), energy, momentum and the
temperature of the moving bodies, and their drift over a run (`team/RESULTS-STANDARD.md`,
section 4). The pressure on the walls is computed by the runner (`runner.wall_pressure`), from
the momentum the walls took.

The energy (E9): `energy_re` is the L0 energy of `energy.py` (Real coordinate); `energy_com` is the
Composer energy of decision D23 where it is defined (L1a with all terms, radial, inertia `Re`, no
second field or background `g`, `e`), `None` otherwise; `energy_total` is the energy the law conserves:
`energy_re` under L0, `energy_re + energy_com` under D23, `None` for a law whose energy is not defined.
"""

import numpy as np

from .constants import Constants
from .energy import composer_energy, energy_l0
from .environment import K_B, kinetic_temperature
from .frame import Frame
from .state import State

__all__ = ["Diagnostics", "drifts"]


class Diagnostics:
    def __init__(
        self,
        frame: Frame,
        constants: Constants,
        softening: float = 0.0,
        background: dict | None = None,
        law=None,
    ):
        self.frame, self.constants, self.softening, self.background = frame, constants, softening, background
        self.law = law  # E9: for the Composer energy (None: the L0 energy only, as before)

    def measure(self, state: State, fields=None) -> dict:
        """One row of measurements. Mass and charge count every body, absorbed ones too."""
        total = state.total_mu(self.frame)
        moving = state.alive & ~state.fixed
        momentum = np.sum(state.m[moving, None] * state.v[moving], axis=0)
        energy = energy_l0(state, self.frame, self.constants, self.softening, self.background)
        com = composer_energy(state, self.law, self.frame, self.constants, self.softening, self.background)
        reads_composer = self.law is not None and getattr(self.law.spec, "reading", "L0") != "L0"
        if com is not None:
            conserved = energy["total"] + com
        else:
            conserved = None if reads_composer else energy["total"]  # L0: the Real energy is the whole energy
        return {
            "t": float(state.t),
            "temperature": kinetic_temperature(state, K_B[self.constants.units]),  # E8.1 (E6b's definition)
            "mass": float(total.re),
            "charge": float(total.com),
            "kinetic": energy["kinetic"],
            "energy_re": energy["total"],
            "energy_com": com,
            "energy_total": conserved,
            "momentum": [float(p) for p in momentum],
            "momentum_scale": float(np.sum(state.m[moving] * np.linalg.norm(state.v[moving], axis=1))),
        }


def _relative(first: float, last: float, scale: float | None = None):
    scale = abs(first) if scale is None else scale
    if scale == 0:
        return 0.0 if last == first else None  # no scale to compare with
    return abs(last - first) / scale


def _maybe(first, last):
    """The relative drift, or None when either value is not defined."""
    return None if first is None or last is None else _relative(first, last)


def drifts(first: dict, last: dict) -> dict:
    """Relative drifts between two measurements. The momentum drift is the change of the
    total momentum divided by the sum of the bodies' `m |v|` (the larger of the two rows)."""
    change = float(np.linalg.norm(np.subtract(last["momentum"], first["momentum"])))
    scale = max(first["momentum_scale"], last["momentum_scale"])
    return {
        "mass": _relative(first["mass"], last["mass"]),
        "charge": _relative(first["charge"], last["charge"]),
        "energy_re": _relative(first["energy_re"], last["energy_re"]),
        "energy_com": _maybe(first.get("energy_com"), last.get("energy_com")),  # E9: None where not defined
        "energy_total": _maybe(first.get("energy_total"), last.get("energy_total")),  # what the law conserves
        "momentum": _relative(0.0, change, scale),
    }
