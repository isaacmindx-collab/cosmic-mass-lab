"""G1: the fast T0 gate, run by pytest in CI on every pull request (decision D3).

Same cases and same pass criteria as the scenarios T0.1 to T0.5, with shorter orbits and a
smaller cloud. The full runs are `scenarios/T0.x/run.py`; their results are in `results/`.
"""

import json

import pytest

from cosmicmass.gates import t0


@pytest.fixture(scope="module")
def gate():
    return t0.run_gate(fast=True)


@pytest.mark.parametrize("test_id", ["T0.1", "T0.2", "T0.3", "T0.4", "T0.5"])
def test_fast_t0_gate(gate, test_id):
    part = gate["parts"][test_id]
    failed = {name: case for name, case in part["cases"].items() if not case["pass"]}
    assert part["pass"], f"{test_id} fails: {json.dumps(failed, default=str)[:600]}"


def test_the_gate_as_a_whole_and_its_references(gate):
    assert gate["pass"] and set(gate["parts"]) == {"T0.1", "T0.2", "T0.3", "T0.4", "T0.5"}
    a, b, c = (gate["parts"]["T0.1"]["cases"][k] for k in "abc")
    assert a["period_analytic"] / 86400 == pytest.approx(27.285, rel=1e-4)  # days
    assert b["period_analytic"] == pytest.approx(1.51942e-16, rel=1e-5)
    assert c["separation_analytic"] == pytest.approx(3.5386e-10, rel=1e-4)
    assert len(gate["parts"]["T0.3"]["cases"]) == len(t0.ANGLES) == 6
    assert gate["parts"]["T0.4"]["cases"]["proton"]["expected"] == pytest.approx(8.13447, rel=1e-6)


def test_the_closed_form_of_the_coulomb_escape():
    # at t = 0 the bodies are at r0; much later they move at the escape speed sqrt(2 k / (mu r0))
    assert t0._escape_radius(0.0, 1.0, -1.0, 1.0) == pytest.approx(1.0)
    late, later = t0._escape_radius(1e6, 1.0, -1.0, 1.0), t0._escape_radius(1.001e6, 1.0, -1.0, 1.0)
    assert (later - late) / 1e3 == pytest.approx(2**0.5, rel=1e-5)


def test_convergence_blocks_and_written_results(tmp_path):
    one = t0.t0_1(periods=0.02, convergence=True)
    assert {"period_eta", "period_eta_half", "period_eta_quarter", "change_half_to_quarter"} == set(
        one["cases"]["a"]["convergence"]
    )
    assert one["cases"]["c"]["convergence"]["change_half_to_quarter"] < 1e-6
    two = t0.t0_2(n=12, steps=30, convergence=True)
    assert set(two["cases"]["cloud"]["convergence"]) == {"eta_half", "eta_quarter", "n_half", "n_double"}
    for outcome in (one, two, t0.t0_4(), t0.t0_5(points_per_side=5)):
        folder = t0.write_gate_result(outcome, out_root=tmp_path, producer="unit test")
        summary = json.loads((folder / "summary.json").read_text())
        stamp = json.loads((folder / "stamp.json").read_text())
        assert (
            summary["scenario"] == outcome["id"] == stamp["scenario"]
            and summary["cases"].keys() == outcome["cases"].keys()
        )
        assert stamp["producer"] == "unit test" and all(s["law"]["id"] == "L0" for s in stamp["cases"].values())
    assert summary["verdict"] == "pass" and (tmp_path / "T0.1").exists()
    assert len(list((tmp_path / "T0.2").glob("*/timeseries-cloud.csv"))) == 1
    failing = dict(t0.t0_5(points_per_side=5), id="T0.5-fail")
    failing["pass"] = False
    assert (
        json.loads((t0.write_gate_result(failing, out_root=tmp_path) / "summary.json").read_text())["verdict"] == "fail"
    )
