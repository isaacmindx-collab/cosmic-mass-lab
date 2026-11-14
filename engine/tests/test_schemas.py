"""P4: the JSON schemas of `stamp.json` and `summary.json` (team/RESULTS-STANDARD.md, sections 2 and 4)."""

import copy
import json
import sys
from pathlib import Path

import pytest

from cosmicmass.gates import t9
from cosmicmass.gates.t0 import write_gate_result
from cosmicmass.runner import run

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import validate_results as vr  # noqa: E402

# Committed summaries that do not follow section 4: their verdict is a sentence, not
# pass / fail / finding. Reported in issue #24; results are never edited by hand, so they
# stay until their producer re-runs them. Nothing else may be wrong with them.
KNOWN_NONCONFORMING = set()  # the D21 verdicts were fixed in #27 (issue #24)


def _settings():
    return {"scenario": "schema-test", "universe": {"phi_bar_deg": 79.86, "dimension": 2, "units": "SI"},
            "law": {"id": "L0"}, "bodies": [{"preset": "proton", "x": [0.0, 0.0]},
                                            {"preset": "electron", "x": [1e-10, 0.0]}],
            "numerics": {"steps": 5, "softening": 0.0}, "kind": "mathematics", "preregistered": False,
            "producer": "test"}


@pytest.mark.parametrize("folder", vr.run_folders(ROOT / "results"), ids=lambda f: f.relative_to(ROOT).as_posix())
def test_committed_results_follow_the_schemas(folder):
    problems = vr.validate_folder(folder)
    scenario = folder.relative_to(ROOT / "results").parts[0]
    if scenario in KNOWN_NONCONFORMING:
        assert len(problems) == 1 and "summary.json: verdict:" in problems[0]
    else:
        assert problems == []


def test_a_fresh_run_validates(tmp_path):
    result = run(_settings(), out_root=tmp_path)
    assert vr.validate_folder(result.folder) == []


def test_a_fresh_test_with_cases_validates(tmp_path):
    for outcome in (t9.t9_4(), t9.t9_2(orbit=False)):
        folder = write_gate_result(outcome, out_root=tmp_path, kind="measurement-check", law="the hypothesis L1a")
        assert vr.validate_folder(folder) == []


def test_an_invalid_stamp_fails_with_a_readable_message():
    stamp = run(_settings(), out_root=None).stamp
    assert vr.validate(stamp, "stamp") == []
    bad = copy.deepcopy(stamp)
    bad["law"]["sign"] = "x"
    del bad["producer"]
    bad["kind"] = "result"
    problems = vr.validate(bad, "stamp")
    assert "law.sign: 'x' is not one of ['+', '-']" in problems
    assert "(top level): 'producer' is a required property" in problems
    assert any(p.startswith("kind: 'result' is not one of") for p in problems)


def test_an_invalid_case_stamp_names_the_case():
    stamp = run(_settings(), out_root=None).stamp
    gate = {"scenario": "T9.9", "run_id": stamp["run_id"], "engine_commit": stamp["engine_commit"],
            "kind": "mathematics", "preregistered": True, "producer": "test", "cases": {"a": stamp}}
    assert vr.validate(gate, "stamp") == []
    gate["cases"]["a"] = dict(stamp, universe=dict(stamp["universe"], dimension=4))
    assert vr.validate(gate, "stamp") == ["cases.a.universe.dimension: 4 is not one of [2, 3]"]


def test_an_invalid_summary_fails():
    summary = run(_settings(), out_root=None).summary
    assert vr.validate(summary, "summary") == []
    assert vr.validate(dict(summary, verdict="maybe"), "summary") == [
        "verdict: 'maybe' is not one of ['pass', 'fail', 'finding', 'none']"]
    cases = {"scenario": "T9.9", "verdict": "none", "explanation": "x", "cases": {"a": {}}}
    assert vr.validate(cases, "summary") == ["verdict: 'none' is not one of ['pass', 'fail', 'finding']"]


def test_the_command_line(tmp_path, capsys):
    folder = run(_settings(), out_root=tmp_path).folder
    assert vr.main([str(tmp_path)]) == 0 and "all valid" in capsys.readouterr().out
    (folder / "summary.json").write_text("{", encoding="utf-8")
    (folder / "stamp.json").unlink()
    assert vr.main([str(tmp_path)]) == 1  # the folder is no longer found: no stamp.json
    (folder / "stamp.json").write_text(json.dumps({"scenario": "x"}), encoding="utf-8")
    assert vr.main([str(folder)]) == 1
    out = capsys.readouterr().out
    assert "not valid JSON" in out and "'run_id' is a required property" in out
    assert vr.main([str(tmp_path / "nothing")]) == 1
