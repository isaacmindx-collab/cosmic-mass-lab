"""L1a, a reading of the Composer coordinate (task E4.3, L1a only). **A hypothesis** (D1).

`docs/05-scenarios-and-tests.md`, section 1, laws:

    L1a:  force = Re(mu E_cal) + lambda s Com(mu E_cal)      (two forces along the field)

The product is the compendium's ("Full product (both coordinates)", applied to the
field `E_cal = g + e G`):

    Com(mu E_cal) = q g + m e + 2 s cos(phi_bar) q e,   with e = -E / s^2,

so the Composer force `lambda s Com` has three terms (option L5):

    "s q g"        s q g                      a charge feels gravity as a field s g
    "-m E/s"       s m e = -m E / s           a mass feels the electric field (the Coupling term)
    "-2 cos q E"   2 s^2 cos q e = -2 cos(phi_bar) q E     the charge share

Options: sign (L2), strength lambda (L3: a number or cos(phi_bar)), terms (L5). The
other readings L1b to L1e and the options L4, L6, L7 and L8 are outside the MVP and
are refused. The Real part is L0, unchanged; with lambda = 0 the law is L0 exactly.
"""

import numpy as np

from ..fields.sample import FieldSample
from ..frame import Frame
from ..state import State
from .base import ForcePair, Law, LawSpec, register
from .l0 import lorentz_argument

__all__ = ["L1a"]


@register
class L1a(Law):
    """Hypothesis: the Composer coordinate of `mu E_cal` acts as a second force along the field."""

    reading = "L1a"
    hypothesis = True

    def __init__(self, spec: LawSpec | None = None):
        super().__init__(spec)
        for option, default in (("direction", "radial"), ("moving", "off"), ("range", "1/r^2")):
            if getattr(self.spec, option) != default:
                raise NotImplementedError(
                    f"L1a: the option {option} = {getattr(self.spec, option)!r} is not implemented yet"
                )

    def strength(self, frame: Frame) -> float:
        """The signed strength: `+/- lambda`, with lambda a number or `cos(phi_bar)` (L3)."""
        lam = frame.cos_phi() if self.spec.strength == "cos_phi_bar" else float(self.spec.strength)
        return lam if self.spec.sign == "+" else -lam

    def composer_coordinate(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """The selected terms of `Com(mu E_cal)`, shape `(N, d)`."""
        m, q = state.m[:, None], state.q[:, None]
        parts = {
            "s q g": q * fields.g,
            "-m E/s": m * fields.e,
            "-2 cos q E": (2 * frame.s * frame.cos_phi()) * (q * fields.e),
        }
        if self.spec.terms == "all":
            return (parts["s q g"] + parts["-m E/s"]) + parts["-2 cos q E"]
        return parts[self.spec.terms]

    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair:
        real = (state.mu(frame)[:, None] * lorentz_argument(state, fields, frame)).re  # L0
        composer = (self.strength(frame) * frame.s) * self.composer_coordinate(state, fields, frame)
        return ForcePair(real=real, composer=composer)
