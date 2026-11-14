"""UI1: the web universe loads exactly the engine's files and its bridge runs the engine unchanged."""

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "simulator" / "web"


def test_manifest_lists_every_engine_file():
    manifest = json.loads((WEB / "engine-files.json").read_text(encoding="utf-8"))
    on_disk = sorted(p.relative_to(ROOT / "engine").as_posix() for p in (ROOT / "engine" / "cosmicmass").rglob("*.py"))
    assert manifest["files"] == on_disk, "regenerate simulator/web/engine-files.json (see simulator/README.md)"
    assert manifest["root"] == "../../engine/"


def test_bridge_runs_a_scene_with_the_engine(monkeypatch):
    import cosmicmass.runner as engine_runner

    # the bridge replaces the runner's `engine_commit` for the browser: put it back after this test, so that
    # the tests that follow write stamps with a real commit (they are checked against the schema since E7.2)
    monkeypatch.setattr(engine_runner, "engine_commit", engine_runner.engine_commit)
    sys.path.insert(0, str(WEB))
    try:
        import bridge
    finally:
        sys.path.remove(str(WEB))
    presets = json.loads(bridge.presets())
    assert presets["proton"]["q"] > 0 and presets["neutron"]["q"] == 0
    earth, moon = presets["Earth"]["m"], presets["moon"]["m"]
    r, total = 3.844e8, earth + moon
    v = math.sqrt(6.67430e-11 * total / r)
    period = 2 * math.pi * math.sqrt(r**3 / (6.67430e-11 * total))
    settings = {
        "scenario": "web-test",
        "universe": {"phi_bar_deg": 79.86, "dimension": 2, "units": "SI"},
        "law": {"id": "L0"},
        "bodies": [
            {"preset": "Earth", "x": [-moon / total * r, 0], "v": [0, -moon / total * v]},
            {"preset": "moon", "x": [earth / total * r, 0], "v": [0, earth / total * v]},
        ],
        "numerics": {"t_end": 0.1 * period, "eta": 1e-3, "softening": 0.0, "record_every": 1},
        "kind": "mathematics",
        "preregistered": False,
    }
    out = json.loads(bridge.run_scene(json.dumps(settings)))
    assert out["law"] == "L0" and out["steps"] > 100
    assert len(out["paths"]) == 2 and len(out["paths"][0]) == len(out["t"]) <= bridge.MAX_FRAMES + 1
    assert out["drift"]["energy_re"] < 1e-9 and out["energy_excursion"] < 1e-9
    assert out["stamp"]["engine_commit"].startswith("web-v")
