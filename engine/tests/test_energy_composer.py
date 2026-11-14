"""E9: the Composer energy of decision D23, and the energy each law conserves."""

import numpy as np
import pytest

from cosmicmass.constants import SCALED
from cosmicmass.diagnostics import Diagnostics, drifts
from cosmicmass.energy import composer_energy, interaction_energy
from cosmicmass.frame import Frame
from cosmicmass.laws import LawSpec, make_law
from cosmicmass.runner import run
from cosmicmass.state import State

FRAME = Frame.scaled()


def pair(q1=0.3, q2=-0.2):
    return State(
        m=[1.0, 2.0],
        q=[q1, q2],
        x=[[0.0, 0.0], [1.5, 0.0]],
        v=[[0.0, 0.0], [0.0, 0.0]],
        fixed=[False, False],
        alive=[True, True],
    )


def l1a(**options):
    return make_law(LawSpec(reading="L1a", **options))


def test_composer_energy_of_two_bodies_by_hand():
    frame = Frame(1.0, np.radians(60.0))  # cos(phi_bar) = 1/2, so the charge share counts
    lam = 0.4
    m1, q1, m2, q2, r = 1.0, 0.3, 2.0, -0.2, 1.5
    com = m1 * q2 + q1 * m2 + 2 * 1.0 * 0.5 * q1 * q2  # Com(mu_1 mu_2), the coefficient of G
    expected = -SCALED.G_N * lam * 1.0 * com / r
    assert composer_energy(pair(), l1a(strength=lam), frame, SCALED) == pytest.approx(expected, rel=1e-14)
    assert composer_energy(pair(), l1a(strength=lam, sign="-"), frame, SCALED) == pytest.approx(-expected, rel=1e-14)


def test_outside_the_scope_of_d23_the_composer_energy_is_not_defined():
    s = pair()
    assert composer_energy(s, make_law(LawSpec(reading="L0")), FRAME, SCALED) is None  # L0 reads no Composer force
    assert composer_energy(s, None, FRAME, SCALED) is None
    for options in ({"terms": "s q g"}, {"direction": "perpendicular"}, {"inertia": "Sh"}, {"moving": "on"}):
        assert composer_energy(s, l1a(**options), FRAME, SCALED) is None, options
    assert composer_energy(s, make_law(LawSpec(reading="L1b")), FRAME, SCALED) is None
    assert composer_energy(s, l1a(), FRAME, SCALED, background={"g": [0.0, -1.0]}) is None
    assert composer_energy(s, l1a(), FRAME, SCALED, background={"B_g": 1.0}) is not None  # no work: allowed


def test_the_diagnostics_report_the_energy_each_law_conserves():
    s = pair()
    under_l0 = Diagnostics(FRAME, SCALED, law=make_law(LawSpec(reading="L0"))).measure(s)
    assert under_l0["energy_com"] is None and under_l0["energy_total"] == under_l0["energy_re"]
    under_l1a = Diagnostics(FRAME, SCALED, law=l1a(strength=0.5)).measure(s)
    assert under_l1a["energy_total"] == pytest.approx(under_l1a["energy_re"] + under_l1a["energy_com"], rel=1e-15)
    assert under_l1a["energy_re"] == pytest.approx(interaction_energy(s, FRAME, SCALED))
    not_defined = Diagnostics(FRAME, SCALED, law=l1a(terms="s q g")).measure(s)
    assert not_defined["energy_com"] is None and not_defined["energy_total"] is None
    assert drifts(not_defined, not_defined)["energy_total"] is None


def orbit(law):
    # an eccentric orbit of two charged bodies (scaled units, 2D): the separation changes a lot, so the
    # Real energy alone is not conserved under L1a, while Real plus Composer is (D23)
    return {
        "scenario": "E9",
        "universe": {"units": "scaled", "dimension": 2, "phi_bar_deg": 60.0},
        "law": law,
        "bodies": [
            {"m": 1.0, "q": 0.3, "x": [0.0, 0.0], "v": [0.0, -0.3]},
            {"m": 1.0, "q": -0.2, "x": [1.0, 0.0], "v": [0.0, 0.3]},
        ],
        "numerics": {"steps": 20000, "softening": 0.0, "eta": 1e-3},
        "kind": "mathematics",
    }


def test_under_l1a_real_plus_composer_is_conserved_and_real_alone_is_not():
    result = run(orbit({"id": "L1a", "lambda": 0.5}), out_root=None)
    drift = result.summary["conservation"]
    assert drift["energy_total"] < 1e-6  # D23: conserved, to the accuracy of the integrator
    assert (
        drift["energy_re"] > 100 * drift["energy_total"]
    )  # the Real part alone exchanges energy with the Composer part
    assert result.summary["final"]["energy_com"] is not None


def test_under_l0_the_total_is_the_real_energy():
    result = run(orbit({"id": "L0"}), out_root=None)
    drift = result.summary["conservation"]
    assert drift["energy_com"] is None and drift["energy_total"] == drift["energy_re"] < 1e-6
