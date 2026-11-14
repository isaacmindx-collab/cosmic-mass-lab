"""L1a-L1d, readings of the Composer coordinate (task E4.3). **Hypotheses** (D1).

`docs/05-scenarios-and-tests.md`, section 1, laws:

    L1a:  force = Re(mu E_cal) + lambda s Com(mu E_cal)        (two forces along the field)
    L1b:  force = Sh(mu E_cal) = Re + s cos(phi_bar) Com
    L1c:  force = Ht(mu E_cal) = s sin(phi_bar) Com
    L1d:  force = abs(mu E_cal) along the field

The product is the compendium's ("Full product (both coordinates)", applied to the field
`E_cal = g + e G`):

    Com(mu E_cal) = q g + m e + 2 s cos(phi_bar) q e,   with e = -E / s^2,

so the Composer coordinate has three terms (option L5):

    "s q g"        s q g                      a charge feels gravity as a field s g
    "-m E/s"       s m e = -m E / s           a mass feels the electric field (the Coupling term)
    "-2 cos q E"   2 s^2 cos q e = -2 cos(phi_bar) q E     the charge share

**One rule for every reading (a labelled choice, `team/notes/E4.md`):** the force is L0's,
`Re[mu (E_cal + v x B_cal)]`, plus `+/- lambda` (L2, L3) times the part that the reading adds to
it. With lambda = 0 every reading is L0 exactly (the reduce-to-L0 test of `ARCHITECTURE.md`,
section 7). Read literally, L1c would drop the Real part, and a pure mass would feel no gravity.
The parts added, for the vector `C` of the selected Composer terms:

    L1a   s C
    L1b   s cos(phi_bar) C                       (Sh minus Re)
    L1c   s sin(phi_bar) C                       (Ht)
    L1d   |A| u - R, with R = Re(mu E_cal), Sh = R + s cos(phi_bar) C, Ht = s sin(phi_bar) C,
          |A| = sqrt(|Sh|^2 + |Ht|^2) and u the unit vector of Sh (of C if Sh is zero): the
          length of the vector `mu E_cal`, along its shadow. Lengths of vectors, not of components,
          so that the force does not depend on the axes.

Options: sign (L2), strength lambda (L3: a number or cos(phi_bar)), terms (L5), inertia (L7:
`Re(mu)`, `Sh(mu)`, `abs(mu)`, in `base.py`). Directions other than radial (L4), the moving-body
term (L6), the screened range (L8) and the reading L1e are not implemented yet and are refused.
"""

import numpy as np

from ..fields.sample import FieldSample
from ..frame import Frame
from ..state import State
from .base import ForcePair, Law, LawSpec, register
from .l0 import lorentz_argument

__all__ = ["L1a", "L1b", "L1c", "L1d"]


class _ComposerReading(Law):
    """L0 plus `+/- lambda` times what a reading of the Composer coordinate adds to it."""

    hypothesis = True

    def __init__(self, spec: LawSpec | None = None):
        super().__init__(spec)
        for option, default in (("direction", "radial"), ("moving", "off"), ("range", "1/r^2")):
            if getattr(self.spec, option) != default:
                raise NotImplementedError(
                    f"{self.reading}: the option {option} = {getattr(self.spec, option)!r} is not implemented yet"
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

    def added(self, real: np.ndarray, composer: np.ndarray, frame: Frame) -> np.ndarray:
        """What the reading adds to L0, for the Real part `real` of `mu E_cal` and its Composer terms."""
        raise NotImplementedError

    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair:
        real = (state.mu(frame)[:, None] * lorentz_argument(state, fields, frame)).re  # L0
        c = self.composer_coordinate(state, fields, frame)
        static = state.m[:, None] * fields.g + (-(frame.s**2)) * state.q[:, None] * fields.e  # Re(mu E_cal)
        return ForcePair(real=real, composer=self.strength(frame) * self.added(static, c, frame))


@register
class L1a(_ComposerReading):
    """Hypothesis: the Composer coordinate of `mu E_cal` acts as a second force along the field."""

    reading = "L1a"

    def added(self, real, composer, frame):
        return frame.s * composer


@register
class L1b(_ComposerReading):
    """Hypothesis: the force is the shadow `Sh(mu E_cal) = Re + s cos(phi_bar) Com`."""

    reading = "L1b"

    def added(self, real, composer, frame):
        return (frame.s * frame.cos_phi()) * composer


@register
class L1c(_ComposerReading):
    """Hypothesis: the Composer coordinate acts through the height `Ht(mu E_cal) = s sin(phi_bar) Com`."""

    reading = "L1c"

    def added(self, real, composer, frame):
        return (frame.s * frame.sin_phi()) * composer


@register
class L1d(_ComposerReading):
    """Hypothesis: the force has the length `abs(mu E_cal)`, along the shadow of the field."""

    reading = "L1d"

    def added(self, real, composer, frame):
        shadow = real + (frame.s * frame.cos_phi()) * composer
        height = (frame.s * frame.sin_phi()) * composer
        length = np.sqrt(np.sum(shadow**2, axis=1) + np.sum(height**2, axis=1))
        size_sh, size_c = np.linalg.norm(shadow, axis=1), np.linalg.norm(composer, axis=1)
        direction = np.zeros_like(shadow)
        use_sh, use_c = size_sh > 0, (size_sh == 0) & (size_c > 0)
        direction[use_sh] = shadow[use_sh] / size_sh[use_sh, None]
        direction[use_c] = composer[use_c] / size_c[use_c, None]
        return length[:, None] * direction - real
