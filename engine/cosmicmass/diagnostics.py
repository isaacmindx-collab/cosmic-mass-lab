"""Conservation diagnostics (task E8.1, MVP part): total cosmic mass (mass and charge),
energy and momentum, and their drift over a run (`team/RESULTS-STANDARD.md`, section 4).

The energy is the L0 energy of `energy.py` (Real coordinate). The Composer energy is
"not defined" until a derivation is approved. Temperature and the pressure on the
walls (E8.1) are outside the MVP.
"""

import numpy as np

from .constants import Constants
from .energy import energy_l0
from .frame import Frame
from .state import State

__all__ = ["Diagnostics", "drifts"]


class Diagnostics:
    def __init__(self, frame: Frame, constants: Constants, softening: float = 0.0, background: dict | None = None):
        self.frame, self.constants, self.softening, self.background = frame, constants, softening, background

    def measure(self, state: State, fields=None) -> dict:
        """One row of measurements. Mass and charge count every body, absorbed ones too."""
        total = state.total_mu(self.frame)
        moving = state.alive & ~state.fixed
        momentum = np.sum(state.m[moving, None] * state.v[moving], axis=0)
        energy = energy_l0(state, self.frame, self.constants, self.softening, self.background)
        return {
            "t": float(state.t),
            "mass": float(total.re),
            "charge": float(total.com),
            "kinetic": energy["kinetic"],
            "energy_re": energy["total"],
            "energy_com": None,
            "momentum": [float(p) for p in momentum],
            "momentum_scale": float(np.sum(state.m[moving] * np.linalg.norm(state.v[moving], axis=1))),
        }


def _relative(first: float, last: float, scale: float | None = None):
    scale = abs(first) if scale is None else scale
    if scale == 0:
        return 0.0 if last == first else None  # no scale to compare with
    return abs(last - first) / scale


def drifts(first: dict, last: dict) -> dict:
    """Relative drifts between two measurements. The momentum drift is the change of the
    total momentum divided by the sum of the bodies' `m |v|` (the larger of the two rows)."""
    change = float(np.linalg.norm(np.subtract(last["momentum"], first["momentum"])))
    scale = max(first["momentum_scale"], last["momentum_scale"])
    return {
        "mass": _relative(first["mass"], last["mass"]),
        "charge": _relative(first["charge"], last["charge"]),
        "energy_re": _relative(first["energy_re"], last["energy_re"]),
        "energy_com": None,  # not defined: needs an approved derivation (E9)
        "momentum": _relative(0.0, change, scale),
    }
