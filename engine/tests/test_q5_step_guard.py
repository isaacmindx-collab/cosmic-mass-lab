"""Q5: the pair guard of rule C and the time loop of the scenario, on a simple two-body case
(not the setups of Q5, whose results are the scenario's)."""

import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.state import State

SPEC = importlib.util.spec_from_file_location("q5", Path(__file__).resolve().parents[2] / "scenarios" / "Q5" / "run.py")
q5 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q5)


def _circle(boost=0.0, t_end=2 * math.pi):
    """Two bodies of mass 1/2 at distance 1 on a circle (scaled units: relative speed 1, period 2 pi)."""
    return {"scenario": "Q5-test", "universe": {"units": "scaled", "dimension": 2}, "law": {"id": "L0"},
            "bodies": [{"m": 0.5, "q": 0.0, "x": [-0.5, 0.0], "v": [boost, -0.5]},
                       {"m": 0.5, "q": 0.0, "x": [0.5, 0.0], "v": [boost, 0.5]}],
            "numerics": {"softening": 0.0, "t_end": t_end}, "kind": "mathematics"}


def test_pair_guard():
    state = State(m=[1.0, 1.0, 1.0], q=[0.0] * 3, x=[[0.0, 0.0], [3.0, 0.0], [0.0, 1.0]],
                  v=[[0.0, 0.0], [0.0, 0.0], [2.0, 0.0]], fixed=[False] * 3, alive=[True] * 3)
    # pairs: (0,1) at rest: ignored; (0,2): 1/2; (1,2): sqrt(10)/2
    assert q5.pair_guard(state, 1e-3) == pytest.approx(1e-3 * 0.5)
    state.alive[2] = False
    assert q5.pair_guard(state, 1e-3) == math.inf


def test_the_loop_ends_on_t_end_and_conserves_energy():
    out = q5.simulate(_circle(), "C", 1e-3)
    assert out["state"].t == 2 * math.pi
    assert np.allclose(out["state"].x, [[-0.5, 0.0], [0.5, 0.0]], atol=1e-4)  # back after one period
    assert out["energy_end_drift"] < 1e-6 and out["energy_largest_excursion"] < 1e-6


def test_rule_c_does_not_depend_on_the_frame():
    own, moved = (q5.simulate(_circle(boost, 0.5), "C", 1e-3) for boost in (0.0, 20.0))
    assert own["steps"] == moved["steps"]
    rel = lambda out: out["state"].x[1] - out["state"].x[0]  # noqa: E731
    assert np.allclose(rel(own), rel(moved), rtol=0, atol=1e-9)
    absolute = q5.simulate(_circle(20.0, 0.5), "A", 1e-3)
    assert absolute["steps"] > 10 * own["steps"]  # rule A pays for the boost (as in Q4)
