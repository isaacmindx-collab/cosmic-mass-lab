"""Energy of the bodies under the reference law L0 (task E9, L0 part only).

Source: compendium, section "Cosmic Mass", paragraph "Cosmic Interaction Law and its
reading": two bodies at rest attract with `F = G Re(mu_a mu_b) / r^2`
`= (G m_a m_b - K q_a q_b) / r^2`. The work of this force gives the interaction energy

    U = - G_N sum_{a<b} Re(mu_a mu_b) / r_ab,

which is the Newton energy plus the Coulomb energy. In a uniform background
`E_cal = g + e G` a body has the energy `- Re[mu E_cal] . x`. With the kinetic energy
`(1/2) Re(mu) v^2` (inertia `Re(mu) = m`), the total is conserved under L0.

Only the Real coordinate is defined here. The energy of the Composer coordinate under
the readings L1 to L8 is not in the compendium: it needs a derivation approved by the
physics lead (`AGENTS.md`, rule 7), and is reported as "not defined".
"""

import numpy as np

from .constants import Constants
from .frame import Frame
from .gnarray import GNArray
from .state import State

__all__ = ["kinetic_energy", "interaction_energy", "background_energy", "energy_l0"]


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
