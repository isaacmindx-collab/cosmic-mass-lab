"""E6b: inflow (U7), the heat bath, fixed sources (U6). Acceptance (docs/WORK-PLAN.md): the inflow
rate within 1% over 10^4 steps; the heat bath holds the temperature within 2%."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.environment import K_B, Environment, HeatBath, Inflow, kinetic_temperature
from cosmicmass.runner import run
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.state import State

ROOT = Path(__file__).resolve().parents[2]
BOX = {"lower": [0.0, 0.0], "upper": [1e-6, 1e-6]}


def _state(n, d=2, m=1.0):
    return State(m=np.full(n, m), q=np.zeros(n), x=np.zeros((n, d)), v=np.zeros((n, d)),
                 fixed=np.zeros(n, dtype=bool), alive=np.ones(n, dtype=bool))


def _settings(**universe):
    return {"scenario": "E6b-test", "universe": {"units": "SI", "dimension": 2, "boundary": "reflecting", "box": BOX,
                                                 **universe},
            "law": {"id": "L0"}, "bodies": [{"preset": "proton", "x": [5e-7, 5e-7], "fixed": True}],
            "numerics": {"adaptive": False, "dt_initial": 1e-10, "steps": 100, "softening": 1e-9},
            "kind": "mathematics", "producer": "test"}


INFLOW = {"preset": "neutron", "rate": 1e9, "velocity": [1e3, 0.0], "face": {"axis": 0, "side": "lower"}}


def test_inflow_rate_within_1_percent_over_ten_thousand_steps():
    rng, state = np.random.default_rng(1), _state(1)
    inflow = Inflow(2.0, 0.5, 37.0, [0.0, -1.0], 1, "upper", [0.0, 0.0], [10.0, 10.0])
    dt = 3.7e-3  # 10^4 steps, about 1369 bodies due
    for _ in range(10_000):
        state.t += dt
        inflow.apply(state, rng)
    expected = 37.0 * state.t
    assert abs(inflow.added / expected - 1) < 0.01 and abs(inflow.added - expected) <= 1
    new = slice(1, None)
    assert state.n == 1 + inflow.added and np.all(state.x[new, 1] == 10.0)  # on the upper face of axis 1
    assert np.all((state.x[new, 0] >= 0) & (state.x[new, 0] <= 10.0)) and np.all(state.v[new] == [0.0, -1.0])
    assert np.all(state.m[new] == 2.0) and np.all(state.q[new] == 0.5) and np.all(state.alive) and not state.fixed.any()


def test_heat_bath_holds_the_temperature_within_2_percent():
    rng = np.random.default_rng(7)
    masses = np.repeat([1.0, 4.0, 1836.0], 400)  # three kinds of body: each must take the bath temperature
    state = State(m=masses, q=np.zeros(1200), x=np.zeros((1200, 3)), v=np.zeros((1200, 3)),
                  fixed=np.zeros(1200, dtype=bool), alive=np.ones(1200, dtype=bool))
    state.v[:400] = 50.0  # start far from the bath: hot light bodies, cold heavy ones
    bath, dt = HeatBath(temperature=2.5, collision_rate=1.0, k_b=1.0), 0.05
    temps, by_kind = [], []
    for step in range(4000):
        bath.apply(state, dt, rng)
        if step >= 2000:  # after 100 collision times
            temps.append(kinetic_temperature(state, 1.0))
            # temperature of each kind: mean of m v^2 over d = 3 (k_B = 1)
            by_kind.append([float(np.mean(masses[s] * np.sum(state.v[s] ** 2, axis=1)) / 3)
                            for s in (slice(0, 400), slice(400, 800), slice(800, 1200))])
    assert abs(np.mean(temps) / 2.5 - 1) < 0.02
    assert np.allclose(np.mean(by_kind, axis=0), 2.5, rtol=0.02)  # equipartition: each mass at the bath temperature


def test_fixed_sources_are_never_touched():
    rng, state = np.random.default_rng(3), _state(3)
    state.fixed[1] = True
    state.v[1] = 0.0
    env = Environment("absorbing", [0, 0], [1, 1], inflow=Inflow(1.0, 0.0, 10.0, [1.0, 0.0], 0, "lower", [0, 0], [1, 1]),
                      heat_bath=HeatBath(1.0, 100.0, 1.0))
    state.x[1] = [5.0, 5.0]  # outside the box: a moving body would be absorbed
    for _ in range(100):
        state.t += 0.01
        env.apply(state, 0.01, rng)
    assert state.alive[1] and np.all(state.v[1] == 0.0) and np.all(state.x[1] == [5.0, 5.0])


def test_kinetic_temperature_and_k_b():
    state = _state(2)
    state.v[:] = [[1.0, 0.0], [0.0, 1.0]]
    assert kinetic_temperature(state, 1.0) == pytest.approx(0.5)  # sum m v^2 / (d N k_B) = 2 / 4
    state.alive[:] = False
    assert kinetic_temperature(state, 1.0) == 0.0
    assert K_B["SI"] == 1.380649e-23 and K_B["scaled"] == 1.0


def test_the_runner_with_inflow_heat_bath_and_a_fixed_source(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import validate_results

    settings = _settings(inflow=INFLOW, heat_bath={"temperature": 300.0, "collision_rate": 1e9})
    result = run(settings, out_root=tmp_path)
    assert result.summary["inflow"] == {"bodies": 10, "m": pytest.approx(10 * 1.67492750e-27), "q": 0.0}
    assert result.summary["heat_bath"]["collisions"] > 0 and result.summary["heat_bath"]["temperature"] == 300.0
    assert result.state.n == 11 and np.all(result.state.x[0] == [5e-7, 5e-7])  # the fixed source stays
    assert "temperature" in result.timeseries[-1] and "x0_0" not in result.timeseries[-1]
    stamp = json.loads((result.folder / "stamp.json").read_text(encoding="utf-8"))
    assert stamp["universe"]["inflow"]["name"] == "neutron" and stamp["universe"]["heat_bath"]["temperature"] == 300.0
    assert validate_results.validate_folder(result.folder) == []
    again = run(settings, out_root=None)  # the same seed gives the same run
    assert np.array_equal(again.state.x, result.state.x) and np.array_equal(again.state.v, result.state.v)
    other = run(dict(settings, numerics=dict(settings["numerics"], seed=1)), out_root=None)
    assert not np.array_equal(other.state.x, result.state.x)


def test_without_inflow_and_bath_nothing_changes():
    result = run(_settings(), out_root=None)
    assert result.summary["inflow"] is None and result.summary["heat_bath"] is None
    assert "temperature" not in result.timeseries[0] and "x0_0" in result.timeseries[0]


@pytest.mark.parametrize("universe,message", [
    ({"boundary": "open", "box": None, "inflow": INFLOW}, "enters a box"),
    ({"inflow": dict(INFLOW, velocity=[-1e3, 0.0])}, "point into the box"),
    ({"inflow": dict(INFLOW, face={"axis": 2, "side": "lower"})}, "face"),
    ({"inflow": dict(INFLOW, face="left")}, "must be an object"),
    ({"inflow": dict(INFLOW, rate=0)}, "rate"),
    ({"inflow": dict(INFLOW, preset="quark")}, "unknown preset"),
    ({"inflow": {"rate": 1.0}}, "give a 'preset'"),
    ({"inflow": dict(INFLOW, colour="red")}, "unknown field"),
    ({"heat_bath": {"temperature": -1.0, "collision_rate": 1.0}}, "positive"),
    ({"heat_bath": {"temperature": 1.0}}, "positive"),
])
def test_bad_settings_are_refused(universe, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(_settings(**universe))


def test_inflow_with_m_and_q_and_the_environment_needs_a_generator():
    spec = dict(INFLOW)
    del spec["preset"]
    s = load_settings(_settings(inflow=dict(spec, m=2e-27, q=1.6e-19, name="ion")))
    assert s.universe["inflow"]["m"] == 2e-27 and s.universe["inflow"]["name"] == "ion"
    env = Environment(heat_bath=HeatBath(1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match="random generator"):
        env.apply(_state(1), 0.1)
    with pytest.raises(ValueError):
        HeatBath(0.0, 1.0, 1.0)
