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
`Re(mu)`, `Sh(mu)`, `abs(mu)`, in `base.py`), and (labelled choices, `team/notes/E4.md`):

- L6, moving bodies: the Composer coordinate of `mu (v x B_cal)`,
  `m (v x b) + q (v x B_g) + 2 s cos(phi_bar) q (v x b)`, is added to the selected terms ("on")
  or used alone ("only"); the Real part of the product used by L1d follows the same choice;
- L4, direction of what is added: "radial" (as computed: along the field), "perpendicular"
  (turned +90 deg in the plane of motion, about z in 3D), "velocity" (its length, along the
  body's velocity; nothing for a body at rest).

- L8, range: "screened" computes the static Composer terms from the field of the bodies
  screened over the Debye length of the population (`fields.direct.debye_length`), with the kernel
  `exp(-r/L) (1 + r/L) / r^2`; L0's Real part is never screened. The screened field is filled by
  the `StepContext` (`FieldSample.screened`).

- L4 "torque" (decision D37): what the reading adds does not push the body but turns its spin,
  with the torque `+/- lambda R |added|` about the axis normal to the plane of motion (`R`, the
  body's radius; a point body gets none). The spin does not act back on the motion.

**L1e** (`docs/05`: "`mu a = mu (E_cal + v x B_cal)` as a General Number equation, so
`a = E_cal + v x B_cal` (motion in two coordinates)"). The body's place is a General Number,
`X = x + xc G` (the optional columns of D37), and its acceleration is the General Number vector

    a = (g + v x B_g) + (e + v x b) G,

the same for every body: the cosmic mass has dropped out. The Real coordinate `x` accelerates
with `g + v x B_g`, the Composer coordinate `xc` with `e + v x b`. With the strength (one rule,
as above): the Real acceleration is L0's plus `lambda (Re(a) - L0's)`, and the Composer
acceleration is `lambda Com(a)`, so that lambda = 1 is the law as written and lambda = 0 is L0
with the Composer coordinate at rest. Labelled choices (`team/notes/E4.md`): the fields are those
at the Real positions `x`; `v` is the Real velocity, as written. An identity worth knowing
(mathematics): `Re(mu a) / Re(mu)` is L0's acceleration, so L0 is the Real reading of `mu a`.
"""

import numpy as np

from ..fields.sample import FieldSample
from ..frame import Frame
from ..state import State
from .base import ForcePair, Law, LawSpec, register
from .l0 import cross, lorentz_argument

__all__ = ["L1a", "L1b", "L1c", "L1d", "L1e", "signed_strength"]


def signed_strength(spec: LawSpec, frame: Frame) -> float:
    """`+/- lambda` (options L2 and L3), with lambda a number or `cos(phi_bar)`."""
    lam = frame.cos_phi() if spec.strength == "cos_phi_bar" else float(spec.strength)
    return lam if spec.sign == "+" else -lam


class _ComposerReading(Law):
    """L0 plus `+/- lambda` times what a reading of the Composer coordinate adds to it."""

    hypothesis = True

    def strength(self, frame: Frame) -> float:
        """The signed strength: `+/- lambda`, with lambda a number or `cos(phi_bar)` (L3)."""
        return signed_strength(self.spec, frame)

    def composer_coordinate(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """The selected terms of `Com(mu E_cal)` (L5), with the moving-body term of L6, shape `(N, d)`.
        With the screened range (L8) the static terms use the screened field of the bodies."""
        m, q = state.m[:, None], state.q[:, None]
        moving = self.moving_coordinate(state, fields, frame)
        if self.spec.moving == "only":
            return moving
        source = fields
        if self.spec.range == "screened":
            if fields.screened is None:
                raise ValueError("the screened range (L8) needs the screened field: use a StepContext")
            source = fields.screened
        parts = {
            "s q g": q * source.g,
            "-m E/s": m * source.e,
            "-2 cos q E": (2 * frame.s * frame.cos_phi()) * (q * source.e),
        }
        if self.spec.terms == "all":
            static = (parts["s q g"] + parts["-m E/s"]) + parts["-2 cos q E"]
        else:
            static = parts[self.spec.terms]
        return static if self.spec.moving == "off" else static + moving

    @staticmethod
    def moving_coordinate(state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """`Com(mu (v x B_cal)) = m (v x b) + q (v x B_g) + 2 s cos(phi_bar) q (v x b)` (L6)."""
        m, q = state.m[:, None], state.q[:, None]
        vb, vbg = cross(state.v, fields.b), cross(state.v, fields.B_g)
        return m * vb + q * vbg + (2 * frame.s * frame.cos_phi()) * (q * vb)

    def real_part(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """The Real part of the same product as the Composer terms (used by L1d)."""
        m, q, s2 = state.m[:, None], state.q[:, None], frame.s**2
        static = m * fields.g - s2 * q * fields.e  # Re(mu E_cal)
        moving = m * cross(state.v, fields.B_g) - s2 * q * cross(state.v, fields.b)  # Re(mu (v x B_cal))
        return {"off": static, "on": static + moving, "only": moving}[self.spec.moving]

    def direct(self, added: np.ndarray, state: State) -> np.ndarray:
        """Option L4: the direction of what is added. With "torque" it pushes nothing: it turns the
        body's spin instead (`torque`)."""
        if self.spec.direction == "radial":
            return added
        if self.spec.direction == "torque":
            return np.zeros_like(added)
        if self.spec.direction == "perpendicular":  # +90 deg in the plane of motion (about z in 3D)
            turned = added.copy()  # in 3D the z component is kept: a turn about z
            turned[:, 0], turned[:, 1] = -added[:, 1], added[:, 0]
            return turned
        speed = np.linalg.norm(state.v, axis=1)  # "velocity": its length, along the velocity
        out = np.zeros_like(added)
        going = speed > 0
        out[going] = (np.linalg.norm(added[going], axis=1) / speed[going])[:, None] * state.v[going]
        return out

    def added(self, real: np.ndarray, composer: np.ndarray, frame: Frame) -> np.ndarray:
        """What the reading adds to L0, for the Real part `real` of `mu E_cal` and its Composer terms."""
        raise NotImplementedError

    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair:
        real = (state.mu(frame)[:, None] * lorentz_argument(state, fields, frame)).re  # L0
        c = self.composer_coordinate(state, fields, frame)
        added = self.direct(self.added(self.real_part(state, fields, frame), c, frame), state)
        return ForcePair(real=real, composer=self.strength(frame) * added)

    def torque(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray | None:
        """Option L4 "torque" (decision D37): what the reading adds does not push the body; it acts at
        the body's surface and turns its spin, with the torque `+/- lambda R |added|` about the axis
        normal to the plane of motion (z; in 3D the torque is along z). `R` is the body's radius: a
        point body (`R = 0`) gets none. `None` for the other directions."""
        if self.spec.direction != "torque":
            return None
        c = self.composer_coordinate(state, fields, frame)
        size = np.linalg.norm(self.added(self.real_part(state, fields, frame), c, frame), axis=1)
        about_z = self.strength(frame) * state.radius * size
        if state.dimension == 2:
            return about_z
        out = np.zeros((state.n, 3))
        out[:, 2] = about_z
        return out


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


@register
class L1e(Law):
    """Hypothesis: `mu a = mu (E_cal + v x B_cal)` as a General Number equation: every body has the
    General Number acceleration `a = E_cal + v x B_cal`, and moves in two coordinates (D37)."""

    reading = "L1e"
    hypothesis = True

    def __init__(self, spec: LawSpec | None = None):
        super().__init__(spec)
        for option, default in (("direction", "radial"), ("terms", "all"), ("moving", "off"), ("range", "1/r^2")):
            if getattr(self.spec, option) != default:
                raise ValueError(f"L1e: the option {option} does not apply to this reading (it has no Composer force)")

    def general_acceleration(self, state: State, fields: FieldSample) -> tuple:
        """The two coordinates of `a = E_cal + v x B_cal`: `(g + v x B_g, e + v x b)`, each `(N, d)`."""
        return fields.g + cross(state.v, fields.B_g), fields.e + cross(state.v, fields.b)

    def forces(self, state: State, fields: FieldSample, frame: Frame) -> ForcePair:
        real = (state.mu(frame)[:, None] * lorentz_argument(state, fields, frame)).re  # L0
        lam = signed_strength(self.spec, frame)
        re_a, _ = self.general_acceleration(state, fields)
        # the Real acceleration is L0's + lambda (Re(a) - L0's): as a force, inertia Re(a) - L0's force
        composer = lam * (self.inertia(state, frame)[:, None] * re_a - real)
        return ForcePair(real=real, composer=composer)

    def composer_acceleration(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        return signed_strength(self.spec, frame) * self.general_acceleration(state, fields)[1]

    def velocity_coupling(self, state: State, fields: FieldSample, frame: Frame) -> np.ndarray:
        """`v x W` is the velocity-dependent force: `(1 - lambda)` of L0's coupling plus `lambda` of
        `inertia B_g` (under `a = E_cal + v x B_cal` the Real velocity turns in `B_g` alone)."""
        lam = signed_strength(self.spec, frame)
        inertia = self.inertia(state, frame)
        l0 = super().velocity_coupling(state, fields, frame)
        own = inertia[:, None] * fields.B_g if fields.B_g.ndim == 2 else inertia * fields.B_g
        return (1.0 - lam) * l0 + lam * own
