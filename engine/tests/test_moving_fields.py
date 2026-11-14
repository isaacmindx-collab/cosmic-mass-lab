"""E2.2: the second field of moving bodies, B_cal = (1/c^2) v x E_cal (decision D41, team/notes/E2.2.md).

Done when (docs/WORK-PLAN.md, E2.2): one moving proton gives the analytic slow-body field within 1e-6,
and B = -s^2 b. Also: two moving charges feel the textbook magnetic force; off by default."""

import sys
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.constants import SI
from cosmicmass.fields import DirectSum
from cosmicmass.frame import Frame
from cosmicmass.laws import LawSpec, make_law
from cosmicmass.matter import preset
from cosmicmass.runner import run
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.state import State

ROOT = Path(__file__).resolve().parents[2]
P = preset("proton")
S2 = SI.K / SI.G_N  # s^2


def moving_proton(v, d=3, fixed=False):
    x = [[0.0] * d]
    return State(m=[P.m], q=[P.q], x=x, v=[v], fixed=[fixed], alive=[True])


POINTS = np.array([[1e-9, 0.0, 0.0], [0.0, 2e-9, 1e-9], [-3e-9, 1e-9, -2e-9]])


def test_one_moving_proton_gives_biot_savart_and_b_is_minus_b_over_s2():
    v = np.array([2e5, -1e5, 3e4])
    field = DirectSum(SI, moving=True).sample(moving_proton(v), POINTS)
    for k, r in enumerate(POINTS):
        dist = np.linalg.norm(r)
        biot_savart = SI.K / SI.c**2 * P.q * np.cross(v, r) / dist**3  # (mu_0 / 4 pi) q v x r_hat / r^2
        B = -S2 * field.b[k]  # Maxwell's B from the Composer coordinate
        assert B == pytest.approx(biot_savart, rel=1e-12, abs=1e-30)
        g = -SI.G_N * P.m * r / dist**3
        assert field.B_g[k] == pytest.approx(np.cross(v, g) / SI.c**2, rel=1e-12, abs=1e-60)


def test_the_static_field_is_unchanged_and_the_option_is_off_by_default():
    v = [2e5, -1e5, 3e4]
    on = DirectSum(SI, moving=True).sample(moving_proton(v), POINTS)
    off = DirectSum(SI).sample(moving_proton(v), POINTS)
    assert np.array_equal(on.g, off.g) and np.array_equal(on.e, off.e)
    assert not off.B_g.any() and not off.b.any()  # without the option: no second field from bodies
    fixed = DirectSum(SI, moving=True).sample(moving_proton(v, fixed=True), POINTS)
    assert not fixed.B_g.any() and not fixed.b.any()  # a fixed body counts as at rest


def test_in_2d_the_second_field_is_the_component_out_of_the_plane():
    v = [2e5, -1e5]
    points2 = POINTS[:, :2]
    in_plane = DirectSum(SI, moving=True).sample(moving_proton(v, d=2), points2)
    three = DirectSum(SI, moving=True).sample(moving_proton([*v, 0.0]), np.c_[points2, np.zeros(len(points2))])
    assert in_plane.b == pytest.approx(three.b[:, 2], rel=1e-12)
    assert in_plane.B_g == pytest.approx(three.B_g[:, 2], rel=1e-12)


def test_two_parallel_moving_bodies_feel_the_textbook_velocity_force():
    # two protons side by side (separation d along y), both moving along x with speed V. Biot-Savart pulls
    # like charges together with K q^2 V^2 / (c^2 d^2); the gravitomagnetic part pushes the masses apart with
    # G m^2 V^2 / (c^2 d^2). On the second body: F_y = (G m^2 - K q^2) V^2 / (c^2 d^2).
    d, V = 1e-9, 3e5
    state = State(
        m=[P.m, P.m], q=[P.q, P.q], x=[[0.0, 0.0, 0.0], [0.0, d, 0.0]], v=[[V, 0, 0], [V, 0, 0]],
        fixed=[False, False], alive=[True, True],
    )  # fmt: skip
    law, frame = make_law(LawSpec()), Frame.si()
    force = {flag: law.forces(state, DirectSum(SI, moving=flag).at_bodies(state), frame).total() for flag in (0, 1)}
    extra = force[1] - force[0]
    expected = (SI.G_N * P.m**2 - SI.K * P.q**2) * V**2 / (SI.c**2 * d**2)
    assert extra[1] == pytest.approx([0.0, expected, 0.0], rel=1e-9, abs=abs(expected) * 1e-12)
    assert extra[0] == pytest.approx([0.0, -expected, 0.0], rel=1e-9, abs=abs(expected) * 1e-12)


def test_settings_option_integrator_and_stamp(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import validate_results

    base = {
        "scenario": "E2.2",
        "universe": {"units": "SI", "dimension": 3, "moving_fields": True},
        "bodies": [
            {"preset": "proton", "x": [0.0, 0.0, 0.0], "v": [1e4, 0.0, 0.0]},
            {"preset": "electron", "x": [1e-9, 0.0, 0.0], "v": [0.0, 1e5, 0.0]},
        ],
        "numerics": {"steps": 5},
    }
    loaded = load_settings(base)
    assert loaded.universe["moving_fields"] is True
    assert loaded.numerics["integrator"] == "boris"  # D10: Boris with a second field, from the bodies now
    assert load_settings({**base, "universe": {"units": "SI", "dimension": 3}}).numerics["integrator"] == "verlet"
    with pytest.raises(SettingsError, match="moving_fields"):
        load_settings({**base, "universe": {"units": "SI", "dimension": 3, "moving_fields": "yes"}})
    result = run(base, out_root=tmp_path)
    assert validate_results.validate_folder(result.folder) == []
    off = run({**base, "universe": {"units": "SI", "dimension": 3}}, out_root=None)
    assert not np.array_equal(result.state.v, off.state.v)  # the second field acts
