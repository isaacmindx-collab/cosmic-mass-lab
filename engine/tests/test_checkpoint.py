"""E7.1 and E7.2, the rest: checkpoints and resuming ("a run interrupted and resumed gives the
same result"), the progress line, step control, the T0 status of the stamp and the check of
the outputs against the P4 schemas. Software checks only: nothing here is a result."""

import copy
import json
import signal
import subprocess

import numpy as np
import pytest

from cosmicmass import checkpoint as checkpoints
from cosmicmass import runner, stamp
from cosmicmass.checkpoint import CheckpointError
from cosmicmass.gates import t0
from cosmicmass.runner import CHECKPOINT_NAME, Interrupted, main, run
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.stamp import ResultsError, engine_commit, t0_status, validate_outputs, write_results

ORBIT = {  # an eccentric pair, adaptive step
    "scenario": "pair",
    "universe": {"units": "scaled", "dimension": 2},
    "law": {"id": "L0"},
    "bodies": [
        {"name": "heavy", "m": 1.0, "q": 0.0, "x": [0.0, 0.0], "v": [0.0, -5e-4]},
        {"name": "light", "m": 1e-3, "q": 0.0, "x": [1.0, 0.0], "v": [0.0, 0.5]},
    ],
    "numerics": {"steps": 300, "softening": 0.0, "eta": 0.02, "record_every": 10},
    "kind": "mathematics",
    "producer": "unit test",
}
GAS = {  # everything that draws random numbers or counts: walls, an inflow, a heat bath, a population
    "scenario": "gas",
    "universe": {
        "units": "scaled",
        "dimension": 2,
        "boundary": "reflecting",
        "box": {"lower": [0.0, 0.0], "upper": [1.0, 1.0]},
        "inflow": {"m": 1e-3, "q": 0.0, "rate": 40.0, "velocity": [0.7, 0.1], "face": {"axis": 0, "side": "lower"}},
        "heat_bath": {"temperature": 1.0, "collision_rate": 8.0},
    },
    "law": {"id": "L0"},
    "populations": [{"m": 1e-3, "q": 1e-3, "n": 12, "temperature": 1.0}],
    "numerics": {"adaptive": False, "dt_initial": 2e-3, "steps": 150, "softening": 0.05, "seed": 7, "record_every": 5},
    "kind": "mathematics",
    "producer": "unit test",
}
ABSORBING = copy.deepcopy(GAS)
ABSORBING["scenario"] = "sink"
ABSORBING["universe"].update(boundary="absorbing", heat_bath=None)
BORIS = {  # a second field: the Boris push, whose remembered acceleration is replaced after the turn
    "scenario": "turn",
    "universe": {"units": "scaled", "dimension": 3, "background": {"B_g": [0.0, 0.0, 2.0], "g": [0.1, 0.0, 0.0]}},
    "law": {"id": "L0"},
    "bodies": [
        {"m": 1.0, "q": 0.0, "x": [0.0, 0.0, 0.0], "v": [1.0, 0.0, 0.2]},
        {"m": 2.0, "q": 0.0, "x": [3.0, 0.0, 0.0], "v": [0.0, 1.0, 0.0]},
    ],
    "numerics": {"adaptive": False, "dt_initial": 0.01, "steps": 120, "softening": 0.1, "record_every": 4},
    "kind": "mathematics",
    "producer": "unit test",
}
L1A = copy.deepcopy(ORBIT)  # a hypothesis of the Composer coordinate, with moving-body terms (L6) and screening (L8)
L1A["scenario"] = "l1a"
L1A["law"] = {"id": "L1a", "lambda": 1e-3, "range": "screened"}
L1A["bodies"][0]["q"], L1A["bodies"][1]["q"] = 1e-3, -1e-3
SCENES = {"orbit": ORBIT, "gas": GAS, "absorbing": ABSORBING, "boris": BORIS, "l1a": L1A}


def with_numerics(settings: dict, **numerics) -> dict:
    out = copy.deepcopy(settings)
    out["numerics"].update(numerics)
    return out


def files(folder) -> tuple:
    return tuple((folder / name).read_bytes() for name in ("summary.json", "timeseries.csv"))


class StopAt:
    """`should_stop` that says yes once, after `step` steps."""

    def __init__(self, step: int):
        self.step, self.calls = step, 0

    def __call__(self) -> bool:
        self.calls += 1
        return self.calls == self.step


# ------------------------------------------------------------------ interrupted and resumed
@pytest.mark.parametrize("scene", sorted(SCENES))
def test_a_run_interrupted_and_resumed_gives_the_same_result(scene, tmp_path):
    settings = with_numerics(SCENES[scene], checkpoint_every=40)
    whole = run(settings, out_root=tmp_path / "whole")
    assert not (tmp_path / "whole" / settings["scenario"] / CHECKPOINT_NAME).exists()  # removed at the end

    out = tmp_path / "cut"
    with pytest.raises(Interrupted) as stopped:  # asked to stop, as Ctrl-C does: not on a checkpoint step
        run(settings, out_root=out, should_stop=StopAt(57))
    saved = out / settings["scenario"] / CHECKPOINT_NAME
    assert stopped.value.step == 57 and stopped.value.checkpoint == saved and saved.exists()
    assert not [p for p in saved.parent.iterdir() if p.is_dir()]  # no results of half a run
    again = run(settings, out_root=out, resume=True)

    assert files(again.folder) == files(whole.folder)  # byte for byte
    assert again.summary == whole.summary and again.timeseries == whole.timeseries
    for name in ("m", "q", "x", "v", "fixed", "alive"):
        assert np.array_equal(getattr(again.state, name), getattr(whole.state, name))
    assert again.state.t == whole.state.t and not saved.exists()
    assert again.stamp["resumed_at_steps"] == [57] and "resumed_at_steps" not in whole.stamp
    assert validate_outputs(again.stamp, again.summary) == []
    assert {k: v for k, v in again.stamp.items() if k not in ("run_id", "resumed_at_steps")} == {
        k: v for k, v in whole.stamp.items() if k != "run_id"
    }


def test_a_killed_run_resumes_from_its_last_periodic_checkpoint(tmp_path):
    settings = with_numerics(GAS, checkpoint_every=25)
    whole = run(settings, out_root=None)

    def crash(row):  # the process dies between two checkpoints
        if row["step"] == 85:
            raise RuntimeError("killed")

    with pytest.raises(RuntimeError):
        run(settings, out_root=tmp_path, progress=crash)
    saved = tmp_path / "gas" / CHECKPOINT_NAME
    assert json.loads(str(np.load(saved)["meta"]))["book"]["step"] == 75
    again = run(settings, out_root=tmp_path, resume=saved)  # the steps 76 to 85 are done again
    assert again.summary == whole.summary and again.timeseries == whole.timeseries
    assert again.stamp["resumed_at_steps"] == [75]


def test_resumed_twice_and_from_a_path(tmp_path):
    settings = with_numerics(GAS, checkpoint_every=25)
    whole = run(settings, out_root=None)
    place = tmp_path / "elsewhere" / "my.npz"
    with pytest.raises(Interrupted):
        run(settings, out_root=None, checkpoint=place, should_stop=StopAt(31))
    with pytest.raises(Interrupted) as second:
        run(settings, out_root=None, checkpoint=place, resume=True, should_stop=StopAt(40))
    assert second.value.step == 71
    done = run(settings, out_root=None, resume=place, checkpoint=place)
    assert done.summary == whole.summary and done.timeseries == whole.timeseries
    assert done.stamp["resumed_at_steps"] == [31, 71] and done.folder is None and not place.exists()
    # the frequency of the checkpoints is not part of the run: a checkpoint may be resumed with another
    with pytest.raises(Interrupted):
        run(settings, out_root=None, checkpoint=place, should_stop=StopAt(10))
    other = run(with_numerics(GAS, checkpoint_every=None), out_root=None, resume=place)
    assert other.summary == whole.summary


def test_without_a_place_nothing_is_written(tmp_path):
    with pytest.raises(Interrupted) as stopped:  # no output folder and no path: stopped, nothing to resume from
        run(ORBIT, out_root=None, should_stop=StopAt(3))
    assert stopped.value.checkpoint is None and "no checkpoint" in str(stopped.value)
    run(with_numerics(ORBIT, checkpoint_every=10), out_root=None)  # asked for, but nowhere to put it
    with pytest.raises(CheckpointError, match="nothing to resume from"):
        run(ORBIT, out_root=None, resume=True)
    plain = run(ORBIT, out_root=tmp_path)  # no checkpoint asked: none written
    assert sorted(p.name for p in plain.folder.parent.iterdir()) == [plain.folder.name]


# ------------------------------------------------------------------ refusals
def test_a_checkpoint_of_another_run_is_refused(tmp_path):
    settings = with_numerics(ORBIT, checkpoint_every=20)
    with pytest.raises(Interrupted):
        run(settings, out_root=tmp_path, should_stop=StopAt(45))
    saved = tmp_path / "pair" / CHECKPOINT_NAME
    with pytest.raises(CheckpointError, match="another run"):
        run(with_numerics(settings, eta=0.01), out_root=tmp_path, resume=True)  # other numerics
    moved = copy.deepcopy(settings)
    moved["bodies"][1]["x"] = [1.5, 0.0]
    with pytest.raises(CheckpointError, match="another run"):
        run(moved, out_root=tmp_path, resume=True)  # other bodies
    assert saved.exists()  # a refusal leaves the checkpoint

    with pytest.raises(CheckpointError, match="no checkpoint at"):
        run(settings, out_root=tmp_path / "empty", resume=True)
    broken = tmp_path / "broken.npz"
    broken.write_bytes(b"not a checkpoint")
    with pytest.raises(CheckpointError, match="cannot be read"):
        run(settings, out_root=None, resume=broken)

    state, cache, arrays, book = checkpoints.load(saved, _key(saved))
    old = tmp_path / "old.npz"
    checkpoints.save(old, _key(saved), state, None, arrays, book)
    content = dict(np.load(old))
    meta = json.loads(str(content["meta"]))
    content["meta"] = np.array(json.dumps(dict(meta, format=0)))
    np.savez(old, **content)
    with pytest.raises(CheckpointError, match="format 0"):
        checkpoints.load(old, _key(saved))
    content["meta"] = np.array(json.dumps(meta))
    content["state.colour"] = np.zeros(2)
    np.savez(old, **content)
    with pytest.raises(CheckpointError, match="colour"):
        checkpoints.load(old, _key(saved))


def _key(path) -> str:
    return json.loads(str(np.load(path)["meta"]))["key"]


def test_a_checkpoint_is_data_and_is_written_whole(tmp_path, monkeypatch):
    settings = with_numerics(L1A, checkpoint_every=20)
    with pytest.raises(Interrupted):
        run(settings, out_root=tmp_path, should_stop=StopAt(41))
    saved = tmp_path / "l1a" / CHECKPOINT_NAME
    with np.load(saved, allow_pickle=False) as data:  # no pickled object in it
        names = set(data.files)
        assert all(data[name].dtype != object for name in names)
    assert {"state.m", "state.x", "state.alive", "cache.a", "cache.fields.g", "cache.fields.screened.e"} <= names
    before = saved.read_bytes()

    def fails(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(np, "savez", fails)  # killed while writing: the previous checkpoint stays whole
    with pytest.raises(OSError):
        run(settings, out_root=tmp_path, resume=True)
    assert saved.read_bytes() == before
    with pytest.raises(TypeError, match="cannot store"):
        checkpoints._plain(object())
    assert checkpoints._plain(np.arange(2)) == [0, 1] and checkpoints._plain(np.float64(0.5)) == 0.5


# ------------------------------------------------------------------ step control
COARSE = with_numerics(ORBIT, adaptive=False, dt_initial=0.05, steps=None, t_end=6.0, record_every=1)


def test_step_control_repeats_a_step_with_half_the_time_step(tmp_path, monkeypatch):
    free = run(COARSE, out_root=None)
    assert free.summary["step_control"] is None and free.summary["stopped_by"] == "t_end"
    held = run(with_numerics(COARSE, drift_tolerance=1e-6), out_root=None)
    control = held.summary["step_control"]
    assert control["drift_tolerance"] == 1e-6 and control["repeated"] > 0 and control["gave_up"] == 0
    assert held.summary["steps"] > free.summary["steps"]  # the shorter steps cover less time each
    assert held.summary["conservation"]["energy_re"] < 0.1 * free.summary["conservation"]["energy_re"]
    steps = [row["dt"] for row in held.timeseries[1:]]
    assert min(steps) < 0.05 and max(steps) == 0.05 and held.state.t == 6.0
    energies = [row["energy_re"] for row in held.timeseries]
    assert all(abs(b - a) <= 1e-6 * abs(a) for a, b in zip(energies, energies[1:]))  # every kept step is within it

    loose = run(with_numerics(COARSE, drift_tolerance=1.0), out_root=None)  # never passed: the same run
    assert loose.summary["step_control"]["repeated"] == 0 and loose.timeseries == free.timeseries

    monkeypatch.setattr(runner, "MAX_HALVINGS", 2)  # a tolerance out of reach: the step is kept, and counted
    hopeless = run(with_numerics(COARSE, drift_tolerance=1e-300, steps=3), out_root=None)
    assert hopeless.summary["step_control"] == {"drift_tolerance": 1e-300, "repeated": 6, "gave_up": 3}
    monkeypatch.undo()
    assert hopeless.summary["stopped_by"] == "steps"

    settings = with_numerics(COARSE, drift_tolerance=1e-6)  # with checkpoints: the same result
    with pytest.raises(Interrupted):
        run(settings, out_root=tmp_path, should_stop=StopAt(50))
    assert run(settings, out_root=tmp_path, resume=True).summary == held.summary


def test_step_control_with_a_run_at_rest():
    still = copy.deepcopy(COARSE)
    still["bodies"] = [{"m": 1.0, "q": 0.0, "x": [0.0, 0.0]}]
    still["numerics"].update(t_end=0.2, drift_tolerance=1e-9)  # no energy: nothing to compare with
    assert run(still, out_root=None).summary["step_control"]["repeated"] == 0


@pytest.mark.parametrize(
    "numerics,message",
    [
        ({"checkpoint_every": 0}, "checkpoint_every"),
        ({"checkpoint_every": 2.5}, "checkpoint_every"),
        ({"checkpoint_every": True}, "checkpoint_every"),
        ({"drift_tolerance": 0}, "drift_tolerance"),
        ({"drift_tolerance": "small"}, "drift_tolerance"),
        ({"drift_tolerance": True}, "drift_tolerance"),
    ],
)
def test_bad_numerics_are_refused(numerics, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(with_numerics(ORBIT, **numerics))


# ------------------------------------------------------------------ progress and the command line
def test_progress_is_called_with_every_row():
    seen = []
    result = run(with_numerics(ORBIT, steps=25), out_root=None, progress=seen.append)
    assert seen == result.timeseries[1:] and [row["step"] for row in seen] == [10, 20, 25]


def _settings_file(tmp_path, settings) -> str:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    return str(path)


def test_command_line_progress_interrupt_and_resume(tmp_path, capsys, monkeypatch):
    settings = with_numerics(GAS, checkpoint_every=50)
    path, out = _settings_file(tmp_path, settings), str(tmp_path / "out")
    whole = run(settings, out_root=None)
    assert main(["run", path, "--out", out, "--resume"]) == 2  # nothing to resume yet
    assert "no checkpoint at" in capsys.readouterr().out

    lines = iter(range(100))

    def interrupting(row):  # Ctrl-C while the run is in its twelfth recorded row
        if next(lines) == 11:
            signal.raise_signal(signal.SIGINT)

    monkeypatch.setattr(runner, "_progress_line", interrupting)
    handler = signal.getsignal(signal.SIGINT)
    assert main(["run", path, "--out", out, "--progress"]) == 130
    assert signal.getsignal(signal.SIGINT) is handler  # the handler is put back
    printed = capsys.readouterr().out
    assert "interrupted after step 60" in printed and "--resume" in printed
    monkeypatch.undo()

    assert main(["run", path, "--out", out, "--resume", "--progress"]) == 0
    printed = capsys.readouterr().out
    assert "step 65: t = 0.13, dt = 0.002, energy (Re) = " in printed and "step 60:" not in printed
    folders = [p for p in (tmp_path / "out" / "gas").iterdir()]
    assert len(folders) == 1 and folders[0].is_dir()  # the results; the checkpoint is gone
    assert json.loads((folders[0] / "summary.json").read_text(encoding="utf-8")) == json.loads(
        json.dumps(whole.summary)
    )
    assert json.loads((folders[0] / "stamp.json").read_text(encoding="utf-8"))["resumed_at_steps"] == [60]

    other = tmp_path / "other.npz"
    assert main(["run", path, "--out", out, "--resume", str(other)]) == 2  # a path of one's own
    assert str(other) in capsys.readouterr().out


def test_command_line_outside_the_main_thread(tmp_path, capsys):
    import threading

    path = _settings_file(tmp_path, with_numerics(ORBIT, steps=5))
    codes = []
    thread = threading.Thread(target=lambda: codes.append(main(["run", path, "--out", str(tmp_path / "out")])))
    thread.start()
    thread.join()
    assert codes == [0] and "results:" in capsys.readouterr().out


# ------------------------------------------------------------------ the outputs are checked (E7.2)
def test_outputs_that_break_the_standard_are_not_written(tmp_path):
    result = run(with_numerics(ORBIT, steps=5), out_root=None)
    assert validate_outputs(result.stamp, result.summary) == []
    bad_stamp = dict(result.stamp, t0_status="maybe", law=dict(result.stamp["law"], sign="?"))
    bad_summary = {k: v for k, v in result.summary.items() if k != "conservation"}
    problems = validate_outputs(bad_stamp, bad_summary)
    assert len(problems) == 3 and problems[0].startswith("stamp.json: law.sign:")
    assert any(p.startswith("stamp.json: t0_status:") for p in problems)
    assert any(p.startswith("summary.json: (top level):") and "conservation" in p for p in problems)
    with pytest.raises(ResultsError, match="law.sign"):
        write_results(tmp_path / "run", bad_stamp, result.summary, result.timeseries)
    assert not (tmp_path / "run").exists()
    cases = {"scenario": "x", "verdict": "pass", "cases": {}, "explanation": "none"}  # the form with cases
    assert any("cases" in p for p in validate_outputs(result.stamp, cases))


def test_without_the_schemas_the_check_is_skipped(tmp_path, monkeypatch):
    result = run(with_numerics(ORBIT, steps=5), out_root=None)
    monkeypatch.setattr(stamp, "_SCHEMAS", tmp_path / "nowhere")
    stamp._validators.cache_clear()
    try:
        assert validate_outputs(dict(result.stamp, t0_status="maybe"), result.summary) is None
        write_results(tmp_path / "run", dict(result.stamp, t0_status="maybe"), result.summary, result.timeseries)
        assert (tmp_path / "run" / "stamp.json").exists()
        import builtins

        real = builtins.__import__

        def no_jsonschema(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError(name)
            return real(name, *args, **kwargs)

        monkeypatch.undo()
        monkeypatch.setattr(builtins, "__import__", no_jsonschema)
        stamp._validators.cache_clear()
        assert validate_outputs(result.stamp, result.summary) is None
    finally:
        monkeypatch.undo()
        stamp._validators.cache_clear()
    assert validate_outputs(result.stamp, result.summary) == []


# ------------------------------------------------------------------ the T0 status of the stamp (E7.2)
def _head() -> str:
    return subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], capture_output=True, text=True).stdout.strip()


def _stored(root, test, run_id, commit, verdict):
    folder = root / test / run_id
    folder.mkdir(parents=True)
    (folder / "stamp.json").write_text(json.dumps({"engine_commit": commit}), encoding="utf-8")
    (folder / "summary.json").write_text(json.dumps({"verdict": verdict}), encoding="utf-8")


def test_t0_status_is_read_from_the_stored_results(tmp_path):
    head = _head()
    if not head:
        pytest.skip("not in a git checkout")
    assert stamp.T0_TESTS == tuple(f"T0.{k}" for k in range(1, 6)) and all(  # the tests of the gate
        hasattr(t0, name.lower().replace(".", "_")) for name in stamp.T0_TESTS
    )
    root = tmp_path / "a"
    assert t0_status(head, root) == "not run"  # nothing stored
    for test in stamp.T0_TESTS[:-1]:
        _stored(root, test, "20260101-000000-" + head, head, "pass")
    stamp._t0_lookup.cache_clear()
    assert t0_status(head, root) == "not run"  # T0.5 is missing
    _stored(root, "T0.5", "20260101-000000-" + head, head, "pass")
    stamp._t0_lookup.cache_clear()
    assert t0_status(head, root) == "pass"
    assert t0_status(head + "-dirty", root) == "not run" and t0_status("unknown", root) == "not run"

    # the newest run on this engine decides; runs on changed files, on an unknown commit, or unreadable, do not count
    _stored(root, "T0.2", "20260102-000000-" + head, head + "-dirty", "fail")
    _stored(root, "T0.2", "20260103-000000-0000000", "0000000", "fail")
    (root / "T0.2" / "20260104-000000-broken").mkdir()
    stamp._t0_lookup.cache_clear()
    assert t0_status(head, root) == "pass"
    _stored(root, "T0.3", "20260105-000000-" + head, head, "fail")
    stamp._t0_lookup.cache_clear()
    assert t0_status(head, root) == "fail"
    _stored(root, "T0.3", "20260106-000000-" + head, head, "finding")  # not a verdict of a gate
    stamp._t0_lookup.cache_clear()
    assert t0_status(head, root) == "not run"
    stamp._t0_lookup.cache_clear()


def test_the_stamp_carries_the_t0_status():
    result = run(with_numerics(ORBIT, steps=2), out_root=None)
    assert result.stamp["t0_status"] == t0_status(engine_commit()) and result.stamp["t0_status"] in (
        "pass",
        "fail",
        "not run",
    )
    assert t0_status() == result.stamp["t0_status"]  # by default: the current engine and the repository's results


def test_t0_status_without_git_installed(monkeypatch):
    def missing(*args, **kwargs):
        raise OSError("git: not found")

    monkeypatch.setattr(subprocess, "run", missing)
    assert stamp._git("status") is None and t0_status("abcdef0") == "not run"


def test_t0_status_outside_git(tmp_path, monkeypatch):
    monkeypatch.setattr(stamp, "_git", lambda *args, **kwargs: None)
    assert t0_status("abcdef0") == "not run"
    _stored(tmp_path, "T0.1", "20260101-000000-abcdef0", "abcdef0", "pass")
    stamp._t0_lookup.cache_clear()
    assert t0_status("abcdef0", tmp_path) == "not run"
    stamp._t0_lookup.cache_clear()
