"""E7.1 to E7.3, E8.1, E9 (L0 part): the runner, the stamp, the command line, the
conservation diagnostics and the L0 energy (compendium, "Cosmic Interaction Law and its
reading": the force G Re(mu_a mu_b) / r^2, whose work is the Newton plus Coulomb energy)."""

import csv
import json
import math
import subprocess
import sys
from datetime import datetime, timezone

import numpy as np
import pytest

from cosmicmass.constants import SI
from cosmicmass.diagnostics import Diagnostics, drifts
from cosmicmass.energy import background_energy, energy_l0, interaction_energy, kinetic_energy
from cosmicmass.frame import Frame
from cosmicmass.matter import preset
from cosmicmass.runner import main, run
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.stamp import engine_commit, make_run_id
from cosmicmass.state import State

SPEED = math.sqrt(1.001)  # circular orbit of masses 1 and 1e-3 at separation 1, scaled units
ORBIT = {
    "scenario": "unit-orbit",
    "universe": {"units": "scaled", "dimension": 2},
    "law": {"id": "L0"},
    "bodies": [
        {"name": "heavy", "m": 1.0, "q": 0.0, "x": [-1e-3 / 1.001, 0.0], "v": [0.0, -1e-3 / 1.001 * SPEED]},
        {"name": "light", "m": 1e-3, "q": 0.0, "x": [1.0 / 1.001, 0.0], "v": [0.0, 1.0 / 1.001 * SPEED]},
    ],
    "numerics": {"t_end": 2.0, "softening": 0.0},
    "kind": "mathematics",
    "producer": "unit test",
}


# ------------------------------------------------------------------ energy (E9)
def test_l0_energy_is_newton_plus_coulomb():
    p, e = preset("proton"), preset("electron")
    state = State.from_bodies([p, e], [[0.0, 0.0, 0.0], [3e-11, 4e-11, 0.0]], v=[[1.0, 2.0, 2.0], [0.0, 0.0, 1e6]])
    f, r = Frame.si(), 5e-11
    assert kinetic_energy(state) == pytest.approx(0.5 * p.m * 9.0 + 0.5 * e.m * 1e12, rel=1e-15)
    expected = -(SI.G_N * p.m * e.m - SI.K * p.q * e.q) / r  # -G m m'/r + K q q'/r
    assert interaction_energy(state, f, SI) == pytest.approx(expected, rel=1e-14)
    assert interaction_energy(state, Frame.si(120.0), SI) == interaction_energy(state, f, SI)  # angle-free
    soft = interaction_energy(state, f, SI, softening=r)
    assert soft == pytest.approx(expected / math.sqrt(2), rel=1e-14)
    parts = energy_l0(state, f, SI)
    assert parts["total"] == parts["kinetic"] + parts["interaction"] and parts["background"] == 0.0
    state.alive[1] = False
    assert interaction_energy(state, f, SI) == 0.0 and kinetic_energy(state) == pytest.approx(0.5 * p.m * 9.0)


def test_background_energy_and_fixed_bodies():
    f = Frame.scaled()
    state = State(
        m=[2.0, 5.0],
        q=[0.5, 0.0],
        x=[[1.0, 3.0], [9.0, 9.0]],
        v=[[0.0, 0.0], [7.0, 7.0]],
        fixed=[False, True],
        alive=[True, True],
    )
    # -Re[mu (g + e G)] . x = -(m g + q E) . x with E = -s^2 e and s = 1
    energy = background_energy(state, f, {"g": [0.0, -10.0], "e": [4.0, 0.0], "b": 3.0})
    assert energy == pytest.approx(-(2.0 * -10.0 * 3.0 + 0.5 * (-4.0) * 1.0))
    assert background_energy(state, f, None) == 0.0 and background_energy(state, f, {"b": 3.0}) == 0.0
    assert kinetic_energy(state) == 0.0  # the fixed body's velocity is not a motion


# ------------------------------------------------------------- diagnostics (E8.1)
def test_diagnostics_and_drifts():
    state = State.from_bodies(
        [preset("proton"), preset("electron"), preset("neutron")],
        [[0.0, 0.0], [1e-10, 0.0], [0.0, 1e-10]],
        v=[[1.0, 0.0], [0.0, 2.0], [3.0, 0.0]],
    )
    d = Diagnostics(Frame.si(), SI)
    first = d.measure(state)
    assert first["mass"] == pytest.approx(sum(preset(k).m for k in ("proton", "electron", "neutron")))
    assert first["charge"] == 0.0 and first["energy_com"] is None and len(first["momentum"]) == 2
    assert first["momentum"][0] == pytest.approx(preset("proton").m + 3 * preset("neutron").m)
    state.alive[1] = False  # an absorbed body still counts in the totals of mass and charge
    later = d.measure(state)
    assert later["mass"] == first["mass"] and later["charge"] == first["charge"]
    assert drifts(first, first) == {
        "mass": 0.0, "charge": 0.0, "energy_re": 0.0, "energy_com": None, "energy_total": 0.0, "momentum": 0.0
    }  # fmt: skip
    changed = dict(first, energy_re=first["energy_re"] * 1.5, momentum=[2 * p for p in first["momentum"]], charge=1e-19)
    out = drifts(first, changed)
    assert (
        out["energy_re"] == pytest.approx(0.5) and out["momentum"] > 0 and out["charge"] is None
    )  # no scale: 0 -> 1e-19


# ------------------------------------------------------- runner and stamp (E7.1, E7.2)
def test_a_run_writes_stamped_results(tmp_path):
    now = datetime(2026, 11, 12, 14, 30, 5, tzinfo=timezone.utc)
    result = run(ORBIT, out_root=tmp_path, now=now)
    commit = engine_commit()
    assert result.folder == tmp_path / "unit-orbit" / f"20261112-143005-{commit}"
    stamp = json.loads((result.folder / "stamp.json").read_text())
    summary = json.loads((result.folder / "summary.json").read_text())
    # the fields of team/RESULTS-STANDARD.md, section 2
    assert set(stamp) == {
        "scenario",
        "run_id",
        "engine_commit",
        "t0_status",
        "law",
        "universe",
        "matter",
        "numerics",
        "environment",
        "kind",
        "preregistered",
        "producer",
    }
    assert stamp["law"]["id"] == "L0" and stamp["universe"] == {
        "phi_bar_deg": 90.0,
        "dimension": 2,
        "units": "scaled",
        "boundary": "open",
        "background": "none",
    }
    assert stamp["matter"] == [
        {"name": "heavy", "m": 1.0, "q": 0.0, "n": 1},
        {"name": "light", "m": 1e-3, "q": 0.0, "n": 1},
    ]
    assert stamp["numerics"]["softening"] == 0.0 and stamp["numerics"]["integrator"] == "verlet"
    assert set(stamp["environment"]) == {"python", "sympy", "mpmath", "numpy"} and stamp["kind"] == "mathematics"
    assert stamp["engine_commit"] == commit and stamp["t0_status"] == "not run"
    # the required measurements of section 4
    drift = summary["conservation"]
    assert drift["mass"] == 0.0 and drift["charge"] == 0.0 and drift["energy_com"] is None
    assert drift["energy_re"] < 1e-6 and drift["momentum"] < 1e-6
    assert summary["t_end"] == 2.0 and summary["steps"] == result.summary["steps"] > 1000 and summary["law"] == "L0"
    assert summary["verdict"] == "none" and summary["convergence"] is None
    with open(result.folder / "timeseries.csv", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["step"] == "0" and float(rows[-1]["t"]) == 2.0 and int(rows[-1]["step"]) == summary["steps"]
    assert {"energy_re", "kinetic", "mass", "charge", "p0", "p1", "x0_0", "v1_1", "dt"} <= set(rows[0])
    angle = math.atan2(
        float(rows[-1]["x1_1"]) - float(rows[-1]["x0_1"]), float(rows[-1]["x1_0"]) - float(rows[-1]["x0_0"])
    )
    assert angle == pytest.approx(2.0 * SPEED, rel=1e-5)  # the pair has turned by omega t
    with pytest.raises(FileExistsError):
        run(ORBIT, out_root=tmp_path, now=now)  # a results folder is never overwritten


def test_the_same_stamp_gives_the_same_summary():
    first, second = run(ORBIT, out_root=None), run(ORBIT, out_root=None)
    assert first.folder is None and json.dumps(first.summary, sort_keys=True) == json.dumps(
        second.summary, sort_keys=True
    )
    assert first.stamp["numerics"] == second.stamp["numerics"]


def test_steps_fixed_step_and_default_softening():
    data = json.loads(json.dumps(ORBIT))
    data["numerics"] = {"steps": 50, "adaptive": False, "dt_initial": 1e-3, "record_every": 10}
    result = run(load_settings(data), out_root=None)
    assert result.summary["steps"] == 50 and result.state.t == pytest.approx(0.05)
    assert [row["step"] for row in result.timeseries] == [0, 10, 20, 30, 40, 50]
    assert result.stamp["numerics"]["softening"] == pytest.approx(1e-3)  # D10: 1e-3 of the separation 1
    data["numerics"] = {"steps": 7, "t_end": 100.0}
    assert run(data, out_root=None).summary["steps"] == 7  # whichever limit comes first
    assert [row["step"] for row in run(data, out_root=None).timeseries] == [0, 1, 2, 3, 4, 5, 6, 7]


def test_free_fall_in_a_background_and_a_reflecting_floor():
    # one body dropped in a uniform g above a reflecting floor: it bounces and keeps its energy
    data = {
        "scenario": "bounce",
        "universe": {
            "units": "scaled",
            "background": {"g": [0.0, -1.0]},
            "boundary": "reflecting",
            "box": {"lower": [-5.0, 0.0], "upper": [5.0, 50.0]},
        },
        "bodies": [{"m": 2.0, "q": 0.0, "x": [0.0, 1.0]}],
        "numerics": {"t_end": 4.5, "dt_max": 1e-3},
    }
    result = run(data, out_root=None)
    assert result.summary["wall_hits"] == 2 and result.summary["conservation"]["energy_re"] < 1e-6
    # two bounces of a body of mass 2 arriving at speed sqrt(2): the floor received 2 * 2 m v downwards
    assert result.summary["wall_impulse"] == pytest.approx([0.0, -8.0 * math.sqrt(2.0)], rel=1e-3)
    assert result.summary["initial"]["energy_re"] == pytest.approx(2.0)  # m g h
    assert result.stamp["universe"]["box"] == {"lower": [-5.0, 0.0], "upper": [5.0, 50.0]}
    assert result.stamp["numerics"]["softening"] == 0.0  # a single body has no separation


def test_a_fixed_source_in_SI_keeps_the_energy():
    data = {
        "scenario": "pinned",
        "bodies": [
            {"preset": "proton", "x": [0.0, 0.0], "fixed": True},
            {"preset": "electron", "x": [5.29177e-11, 0.0], "v": [0.0, 2.18769e6]},
        ],
        "numerics": {"steps": 3000, "softening": 0.0},
    }
    result = run(data, out_root=None)
    assert result.summary["conservation"]["energy_re"] < 1e-6
    assert np.array_equal(result.state.x[0], [0.0, 0.0])
    assert result.stamp["matter"][0] == {"name": "proton", "m": preset("proton").m, "q": preset("proton").q, "n": 1}
    assert result.stamp["universe"]["units"] == "SI" and result.stamp["universe"]["phi_bar_deg"] == 79.86


def test_runs_that_cannot_stop_or_step_are_refused():
    data = json.loads(json.dumps(ORBIT))
    data["numerics"] = {}
    with pytest.raises(SettingsError, match="steps"):
        run(data, out_root=None)
    data["numerics"] = {"steps": 5, "adaptive": False}
    with pytest.raises(SettingsError, match="dt_initial"):
        run(data, out_root=None)


def test_run_id_and_engine_commit():
    assert make_run_id("ab12cd3", datetime(2026, 11, 12, 14, 30, 5, tzinfo=timezone.utc)) == "20261112-143005-ab12cd3"
    assert make_run_id("ab12cd3").endswith("-ab12cd3") and len(make_run_id("ab12cd3")) == 23
    commit = engine_commit()
    assert commit == "unknown" or len(commit.removesuffix("-dirty")) == 7


def test_engine_commit_outside_git(monkeypatch):
    def no_git(*args, **kwargs):
        raise OSError("git is not installed")

    monkeypatch.setattr(subprocess, "run", no_git)
    assert engine_commit() == "unknown"


# ------------------------------------------------------------- command line (E7.3)
def test_command_line(tmp_path, capsys):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({**ORBIT, "numerics": {"steps": 20, "softening": 0.0}}), encoding="utf-8")
    assert main(["run", str(path), "--out", str(tmp_path / "out")]) == 0
    printed = capsys.readouterr().out
    assert "scenario unit-orbit, law L0: 20 steps" in printed and "results:" in printed
    assert len(list((tmp_path / "out" / "unit-orbit").glob("*/stamp.json"))) == 1
    assert main(["run", str(tmp_path / "missing.json")]) == 2 and "error:" in capsys.readouterr().out
    path.write_text(json.dumps({**ORBIT, "numerics": {}}), encoding="utf-8")
    assert main(["run", str(path), "--out", str(tmp_path / "out")]) == 2


def test_python_dash_m_cosmicmass(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({**ORBIT, "numerics": {"steps": 5, "softening": 0.0}}), encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-m", "cosmicmass", "run", str(path), "--out", str(tmp_path / "out")],
        capture_output=True,
        text=True,
    )
    assert done.returncode == 0 and "5 steps" in done.stdout
    assert (next((tmp_path / "out" / "unit-orbit").iterdir()) / "summary.json").exists()
