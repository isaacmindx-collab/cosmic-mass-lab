"""T9.1, T9.3 and T9.4 as fast checks: the engine reproduces the book's statements under L1a
(decision D4). The stamped runs are `scenarios/T9.1/run.py`, `scenarios/T9.3/run.py` and
`scenarios/T9.4/run.py`."""

import json

import pytest

from cosmicmass.gates import t9
from cosmicmass.gates.t0 import write_gate_result


def test_t9_1_neutron_effective_charge():
    case = t9.t9_1()["cases"]["neutron"]
    assert case["pass"] and case["q_eff_in_e"] == pytest.approx(-9.009e-19, rel=1e-4)  # book: 9.0e-19 e
    assert case["standard_errors_from_measurement"] == pytest.approx(1126, rel=1e-3)  # "about eleven hundred"
    assert case["largest_strength_allowed_at_two_standard_errors"] == pytest.approx(0.0020, rel=1e-2)  # "about 0.002"
    assert case["composer_force"][0] < 0 and case["composer_force"][1] == 0.0  # pulled towards the proton
    small = t9.t9_1(strength=0.002)["cases"]["neutron"]  # the response is proportional to lambda
    assert small["pass"] and small["q_eff_in_e"] == pytest.approx(0.002 * case["q_eff_in_e"], rel=1e-12)
    assert t9.t9_1(phi_bar_deg=120.0)["cases"]["neutron"]["q_eff_coulomb"] == case["q_eff_coulomb"]  # no angle in it


def test_t9_3_equivalent_field_of_gravity():
    case = t9.t9_3()["cases"]["electron"]
    assert case["pass"] and case["equivalent_field_size"] == pytest.approx(1.1380e11, rel=1e-4)  # book: 1.14e11 V/m
    assert case["equivalent_field_V_per_m"][1] < 0 and case["equivalent_field_V_per_m"][0] == 0.0  # along g
    assert case["composer_over_real"] > 1e21  # far larger than the weight of the electron


def test_t9_4_particle_and_antiparticle_pushed_opposite_ways():
    outcome = t9.t9_4()
    p, a, pair = (outcome["cases"][k] for k in ("proton", "antiproton", "pair"))
    assert outcome["pass"] and all(pair["checks"].values())
    assert p["composer_force"][0] < 0 < a["composer_force"][0]  # proton pulled to the Earth, antiproton pushed away
    assert p["composer_size"] == pytest.approx(1.51237e-8, rel=1e-5)  # s e g at 7e6 m
    assert p["composer_over_real"] == pytest.approx(1.1116e18, rel=1e-4)  # s e / m_p
    assert p["real_force"] == a["real_force"]  # they fall alike under L0
    assert t9.t9_4(phi_bar_deg=120.0)["cases"]["proton"]["composer_force"] == p["composer_force"]  # no angle in it
    off = t9.t9_4(strength=0.0)["cases"]
    assert off["proton"]["composer_force"] == [0.0, 0.0] and off["antiproton"]["composer_force"] == [0.0, 0.0]


def test_results_are_written_as_measurement_checks(tmp_path):
    for outcome in (t9.t9_4(), t9.t9_1(), t9.t9_3()):
        folder = write_gate_result(outcome, out_root=tmp_path, kind="measurement-check", law="the hypothesis L1a")
        stamp = json.loads((folder / "stamp.json").read_text())
        summary = json.loads((folder / "summary.json").read_text())
        assert stamp["kind"] == "measurement-check" and "hypothesis L1a" in summary["explanation"]
        assert all(s["law"]["id"] == "L1a" and s["kind"] == "measurement-check" for s in stamp["cases"].values())
    assert stamp["cases"]["electron"]["law"]["terms"] == "s q g"
