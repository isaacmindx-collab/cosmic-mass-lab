"""Results standard, section 1: every run lives in `results/<ID>/<run-id>/` (or one level deeper for a
law, as in `results/T1.4/L0/<run-id>/`), and the folder is named after the `run_id` of its stamp.

Added after a slip in pull request #27: four D21 runs were copied into `results/D21.x/` itself, which
the schema validator does not see (it validates any folder holding a `stamp.json`).
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
RUN_ID = re.compile(r"^\d{8}-\d{6}-[0-9a-z.-]+$")


def _stamps():
    return sorted(RESULTS.rglob("stamp.json"))


def test_there_are_results():
    assert _stamps()


def test_every_run_sits_in_a_folder_named_after_its_run_id():
    problems = []
    for stamp_path in _stamps():
        folder = stamp_path.parent
        depth = len(folder.relative_to(RESULTS).parts)
        if depth not in (2, 3):
            problems.append(f"{folder.relative_to(ROOT)}: expected results/<ID>/<run-id>/")
            continue
        if not RUN_ID.match(folder.name):
            problems.append(f"{folder.relative_to(ROOT)}: folder name is not a run id")
            continue
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
        if stamp.get("run_id") != folder.name:
            problems.append(f"{folder.relative_to(ROOT)}: stamp run_id is {stamp.get('run_id')!r}")
    assert problems == []


def test_no_loose_files_beside_run_folders():
    loose = [p.relative_to(ROOT) for scenario in RESULTS.iterdir() if scenario.is_dir()
             for p in scenario.iterdir() if p.is_file()]
    assert loose == []
