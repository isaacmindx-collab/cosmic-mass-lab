"""Energy of the bodies in both coordinates (task E9).

Source: compendium, section "Cosmic Mass", paragraph "Cosmic Interaction Law and its
reading": two bodies at rest attract with `F = G Re(mu_a mu_b) / r^2`
`= (G m_a m_b - K q_a q_b) / r^2`. The work of this force gives the interaction energy

    U = - G_N sum_{a<b} Re(mu_a mu_b) / r_ab,

which is the Newton energy plus the Coulomb energy. In a uniform background
`E_cal = g + e G` a body has the energy `- Re[mu E_cal] . x`. With the kinetic energy
`(1/2) Re(mu) v^2` (inertia `Re(mu) = m`), the total is conserved under L0.

The Composer coordinate (`composer_energy`). The compendium does not define it; the approved
derivation is **decision D23** (proposed answer to question 1 of `team/QUESTIONS.md`): under the
reading L1a with all terms, the radial direction, inertia `Re(mu)` and no second field, the field of
a body at rest makes the pair force `-G [Re + lambda s Com](mu_a mu_b) r_ab / r^3`, central and equal
and opposite because the product of General Numbers commutes. Its potential is therefore

    U_com = - G_N lambda s sum_{a<b} Com(mu_a mu_b) / r_ab,

with `Com(mu_a mu_b) = m_a q_b + q_a m_b + 2 s cos(phi_bar) q_a q_b` (the coefficient of `G`) and the
signed strength `lambda` (options L2, L3), and `kinetic + U_re + U_com` is conserved. Outside that
scope (other readings or options, or uniform background fields `g`, `e`, which D23 does not cover)
the Composer energy is **not defined** and is reported as `None`; the single-term options of L5 are
not reciprocal (scenario Q1) and have no such energy.
"""

import numpy as np

from .constants import Constants
from .frame import Frame
from .gnarray import GNArray
from .state import State

__all__ = ["kinetic_energy", "interaction_energy", "background_energy", "energy_l0", "composer_energy", "D23_SCOPE"]

# decision D23: the options under which the Composer energy is defined (with no background g or e)
D23_SCOPE = {
    "reading": "L1a",
    "terms": "all",
    "direction": "radial",
    "inertia": "Re",
    "moving": "off",
    "range": "1/r^2",
}


def kinetic_energy(state: State) -> float:
    """`(1/2) sum m v^2` over the moving bodies (alive and not fixed)."""
    moving = state.alive & ~state.fixed
    return float(0.5 * np.sum(state.m[moving] * np.sum(state.v[moving] ** 2, axis=1)))


def interaction_energy(state: State, frame: Frame, constants: Constants, softening: float = 0.0) -> float:
    """`- G_N sum_{a<b} Re(mu_a mu_b) / sqrt(r_ab^2 + eps^2)` over the alive bodies. The
    softening length `eps` is the one of the field solver, so that force and energy agree."""
    idx = np.flatnonzero(state.alive)
    if len(idx) < 2:
        return 0.0
    mu = GNArray(state.m[idx], state.q[idx], frame)
    strength = (mu[:, None] * mu[None, :]).re  # Re(mu_a mu_b) = m_a m_b - s^2 q_a q_b
    diff = state.x[idx][:, None, :] - state.x[idx][None, :, :]
    dist = np.sqrt(np.einsum("abd,abd->ab", diff, diff) + softening**2)
    upper = np.triu_indices(len(idx), k=1)
    return float(-constants.G_N * np.sum(strength[upper] / dist[upper]))


def background_energy(state: State, frame: Frame, background: dict | None) -> float:
    """`- sum Re[mu (g + e G)] . x` for uniform background fields `g` and `e`. The second
    field does no work and has no energy term here."""
    if not background or not ({"g", "e"} & set(background)):
        return 0.0
    moving = state.alive & ~state.fixed
    d = state.dimension
    field = GNArray(
        np.asarray(background.get("g", np.zeros(d)), dtype=float),
        np.asarray(background.get("e", np.zeros(d)), dtype=float),
        frame,
    )
    force = (GNArray(state.m[moving], state.q[moving], frame)[:, None] * field).re  # Re[mu E_cal]
    return float(-np.sum(force * state.x[moving]))


def composer_energy(
    state: State, law, frame: Frame, constants: Constants, softening: float = 0.0, background: dict | None = None
) -> float | None:
    """The Composer energy `- G_N lambda s sum_{a<b} Com(mu_a mu_b) / sqrt(r_ab^2 + eps^2)` of decision D23,
    or `None` where it is not defined: a law outside `D23_SCOPE` (L0 reads no Composer force at all),
    or uniform background fields `g`, `e`. The softening is the field solver's, as for the Real part."""
    spec = getattr(law, "spec", None)
    if spec is None or any(getattr(spec, key) != value for key, value in D23_SCOPE.items()):
        return None
    if background and any(np.any(np.asarray(background.get(key, 0.0)) != 0) for key in ("g", "e")):
        return None
    idx = np.flatnonzero(state.alive)
    if len(idx) < 2:
        return 0.0
    mu = GNArray(state.m[idx], state.q[idx], frame)
    coupling = (mu[:, None] * mu[None, :]).com  # Com(mu_a mu_b): the coefficient of G
    diff = state.x[idx][:, None, :] - state.x[idx][None, :, :]
    dist = np.sqrt(np.einsum("abd,abd->ab", diff, diff) + softening**2)
    upper = np.triu_indices(len(idx), k=1)
    return float(-constants.G_N * law.strength(frame) * frame.s * np.sum(coupling[upper] / dist[upper]))


def energy_l0(
    state: State, frame: Frame, constants: Constants, softening: float = 0.0, background: dict | None = None
) -> dict:
    """The parts of the L0 energy and their total."""
    parts = {
        "kinetic": kinetic_energy(state),
        "interaction": interaction_energy(state, frame, constants, softening),
        "background": background_energy(state, frame, background),
    }
    parts["total"] = parts["kinetic"] + parts["interaction"] + parts["background"]
    return parts
