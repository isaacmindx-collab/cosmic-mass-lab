"""E3.2: the Boris push for `v x B_cal` (D10). Done when (docs/WORK-PLAN.md): gyration in uniform `b`
has radius and period within 1e-6, and the speed is constant. Law L0; checks against mathematics."""

import math

import numpy as np
import pytest

from cosmicmass.constants import SI
from cosmicmass.integrators import Boris, StepContext, VelocityVerlet, boris_rotation
from cosmicmass.matter import preset
from cosmicmass.runner import run
from cosmicmass.settings import SettingsError, load_settings

S = SI.s
P = preset("proton")


def _gyration(dimension=2, periods=1.0):
    """A proton at the origin, speed 1e5 m/s along x, in a uniform field B = 5 nT out of the plane
    (b = -B / s^2). Its rotation rate is Omega = q B / m."""
    B = 5e-9
    omega = P.q * B / P.m
    b = -B / S**2
    background = {"b": b} if dimension == 2 else {"b": [0.0, 0.0, b]}
    v0 = [1e5, 0.0] if dimension == 2 else [1e5, 0.0, 0.0]
    settings = {
        "scenario": "E3.2",
        "universe": {"dimension": dimension, "units": "SI", "background": background},
        "law": {"id": "L0"},
        "bodies": [{"preset": "proton", "x": [0.0] * dimension, "v": v0}],
        # a lone body has no neighbour and does not limit the step: dt_max gives it eta / Omega
        "numerics": {"t_end": periods * 2 * math.pi / omega, "dt_max": 1e-3 / omega, "record_every": 1},
        "kind": "mathematics",
    }
    return settings, omega, 1e5 / omega


@pytest.mark.parametrize("dimension", [2, 3])
def test_gyration_in_uniform_b_radius_period_and_speed(dimension):
    settings, omega, radius = _gyration(dimension)
    result = run(settings, out_root=None)
    assert result.stamp["numerics"]["integrator"] == "boris"  # chosen by D10 because b is not zero
    x = np.array([[r["x0_0"], r["x0_1"]] for r in result.timeseries])
    v = np.array([[r["v0_0"], r["v0_1"]] for r in result.timeseries])
    centre = np.array([0.0, -radius])  # v x Omega with Omega > 0 out of the plane turns +x towards -y
    assert np.max(np.abs(np.linalg.norm(x - centre, axis=1) / radius - 1)) < 1e-6  # radius
    assert np.max(np.abs(np.linalg.norm(v, axis=1) / 1e5 - 1)) < 1e-12  # speed constant
    # after one period the proton is back where it started: the period is right to 1e-6
    assert np.linalg.norm(x[-1]) / (2 * math.pi * radius) < 1e-6


def test_e_cross_b_drift_moves_straight():
    # uniform E along x and B out of the plane: a charge moving at E x B / B^2 feels no force
    E, B = 1e-3, 5e-9
    drift = [0.0, -E / B]  # E x B / B^2 with E along x, B along z
    settings = {
        "scenario": "E3.2",
        "universe": {"dimension": 2, "units": "SI", "background": {"e": [-E / S**2, 0.0], "b": -B / S**2}},
        "law": {"id": "L0"},
        "bodies": [{"preset": "proton", "x": [0.0, 0.0], "v": drift}],
        "numerics": {"t_end": 50.0, "dt_max": 1e-3 * P.m / (P.q * B), "record_every": 1},
        "kind": "mathematics",
    }
    result = run(settings, out_root=None)
    v = np.array([[r["v0_0"], r["v0_1"]] for r in result.timeseries])
    assert np.max(np.abs(v - drift)) / abs(drift[1]) < 1e-9
    assert result.state.x[0] == pytest.approx([0.0, drift[1] * 50.0], rel=1e-9, abs=1e-6)


def test_a_neutral_mass_turns_in_b_g():
    # the second field of gravity: a neutral body gyrates with Omega = B_g
    Bg = 2.0
    settings = {
        "scenario": "E3.2",
        "universe": {"dimension": 2, "units": "scaled", "background": {"B_g": Bg}},
        "law": {"id": "L0"},
        "bodies": [{"m": 1.0, "q": 0.0, "x": [0.0, 0.0], "v": [1.0, 0.0]}],
        "numerics": {"t_end": math.pi, "dt_max": 1e-3 / Bg},  # one period: 2 pi / Omega
        "kind": "mathematics",
    }
    result = run(settings, out_root=None)
    assert np.linalg.norm(result.state.x[0]) < 1e-6 and np.linalg.norm(result.state.v[0]) == pytest.approx(1.0)


def test_without_a_second_field_boris_is_velocity_verlet():
    settings = {
        "scenario": "E3.2",
        "universe": {"dimension": 2, "units": "scaled"},
        "law": {"id": "L0"},
        "bodies": [
            {"m": 1.0, "q": 0.0, "x": [-0.5, 0.0], "v": [0.0, -0.5]},
            {"m": 1.0, "q": 0.3, "x": [0.5, 0.0], "v": [0.0, 0.5]},
        ],
        "numerics": {"t_end": 2.0, "softening": 0.0},
        "kind": "mathematics",
    }
    verlet = run(settings, out_root=None)
    boris = run({**settings, "numerics": {**settings["numerics"], "integrator": "boris"}}, out_root=None)
    assert verlet.stamp["numerics"]["integrator"] == "verlet"
    assert verlet.summary["steps"] == boris.summary["steps"]
    # the same method: two quarter kicks instead of one half kick differ only by rounding, accumulated
    # over the steps (about 1e-14 here)
    assert np.allclose(verlet.state.x, boris.state.x, rtol=0, atol=1e-12)
    assert np.allclose(verlet.state.v, boris.state.v, rtol=0, atol=1e-12)


def test_boris_rotation_keeps_the_speed_and_turns_by_the_right_angle():
    rng = np.random.default_rng(1)
    v, omega = rng.normal(size=(5, 3)), rng.normal(size=(5, 3))
    turned = boris_rotation(v, omega, 0.1)
    assert np.allclose(np.linalg.norm(turned, axis=1), np.linalg.norm(v, axis=1), rtol=1e-14)
    v2 = np.array([[1.0, 0.0]])
    angle = math.atan2(*boris_rotation(v2, np.array([0.3]), 0.5)[0][::-1])
    assert angle == pytest.approx(-2 * math.atan(0.3 * 0.5 / 2), rel=1e-14)  # clockwise, 2 atan(Omega h / 2)


def test_integrator_settings_and_refusals():
    base = {"scenario": "x", "bodies": [{"preset": "proton", "x": [0.0, 0.0]}]}
    assert load_settings(base).numerics["integrator"] == "verlet"
    assert load_settings({**base, "universe": {"background": {"g": [0.0, -1.0]}}}).numerics["integrator"] == "verlet"
    assert load_settings({**base, "universe": {"background": {"B_g": 1e-9}}}).numerics["integrator"] == "boris"
    explicit = load_settings({**base, "universe": {"background": {"b": 1.0}}, "numerics": {"integrator": "verlet"}})
    assert explicit.numerics["integrator"] == "verlet"  # an explicit choice is kept
    with pytest.raises(SettingsError, match="integrator"):
        load_settings({**base, "numerics": {"integrator": "leapfrog"}})

    class Law:  # a law that reads the Composer coordinate of mu (v x B_cal) (L6 on): not for Boris
        class spec:
            moving = "on"

    s = load_settings(base)
    ctx = StepContext(Law(), None, s.frame)
    with pytest.raises(NotImplementedError, match="L6"):
        Boris().step(s.state, 1.0, ctx)
    ctx = StepContext(s.make_law(), None, s.frame)
    with pytest.raises(ValueError, match="remember"):
        ctx.remember(s.state, np.zeros((1, 2)))
    assert isinstance(Boris(), VelocityVerlet)
