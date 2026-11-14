"""Decision D37: the optional columns of `State` (`xc`, `vc`, `spin`, `radius`), the reading L1e
(motion in two coordinates) and the direction "torque" of L4. L1e and the torque are hypotheses (D1);
these are checks of the engine against the formulas of `laws/l1.py`."""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.constants import SCALED
from cosmicmass.fields import DirectSum, FieldSample
from cosmicmass.frame import Frame
from cosmicmass.integrators import Boris, StepContext, VelocityVerlet
from cosmicmass.laws import LawSpec, make_law
from cosmicmass.runner import run
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.state import State

ROOT = Path(__file__).resolve().parents[2]


def one_body(m=1.0, q=1.0, v=(0.0, 0.0), d=2, **columns):
    zeros = [0.0] * d
    return State(m=[m], q=[q], x=[zeros], v=[list(v) + zeros[len(v) :]], fixed=[False], alive=[True], **columns)


def hand_case():
    """m = 3, q = 5, v = (2, -1) in the frame s = 2, 60 deg, with g = (7, 0), e = (0, 11), B_g = 3, b = 0.5."""
    f = Frame.from_degrees(2.0, 60.0)
    state = State(m=[3.0], q=[5.0], x=[[0.0, 0.0]], v=[[2.0, -1.0]], fixed=[False], alive=[True])
    fields = FieldSample(np.array([[7.0, 0.0]]), np.array([[0.0, 11.0]]), np.array([3.0]), np.array([0.5]))
    return f, state, fields


# ------------------------------------------------------------------ the columns of State
def test_state_optional_columns_default_to_zero_and_are_copied():
    state = State(m=[1.0, 2.0], q=[0.0, 1.0], x=[[0.0, 0.0], [1.0, 0.0]], v=[[0.0, 0.0]] * 2, fixed=[False] * 2,
                  alive=[True] * 2)  # fmt: skip
    assert state.xc.shape == state.vc.shape == (2, 2) and state.spin.shape == state.radius.shape == (2,)
    assert not (state.xc.any() or state.vc.any() or state.spin.any() or state.radius.any())
    space = State(m=[1.0], q=[0.0], x=[[0.0] * 3], v=[[0.0] * 3], fixed=[False], alive=[True], radius=[0.5])
    assert space.spin.shape == (1, 3) and space.radius[0] == 0.5
    copy = space.copy()
    copy.xc[0, 0], copy.spin[0, 2], copy.radius[0] = 9.0, 9.0, 9.0
    assert not space.xc.any() and not space.spin.any() and space.radius[0] == 0.5
    for bad in ({"xc": [[0.0]]}, {"spin": [[0.0, 0.0]]}, {"radius": [-1.0]}, {"vc": [0.0, 0.0]}):
        with pytest.raises(ValueError):
            one_body(**bad)


def test_extend_appends_bodies_with_every_column():
    state = one_body(radius=[0.3], xc=[[1.0, 2.0]])
    state.extend([2.0, 3.0], [0.0, -1.0], [[1.0, 1.0], [2.0, 2.0]], [[0.0, 1.0], [0.0, 2.0]])
    assert state.n == 3 and list(state.m) == [1.0, 2.0, 3.0] and list(state.alive) == [True] * 3
    assert state.xc.shape == state.vc.shape == (3, 2) and state.spin.shape == state.radius.shape == (3,)
    assert list(state.xc[0]) == [1.0, 2.0] and state.radius[0] == 0.3 and not state.xc[1:].any()
    space = one_body(d=3)
    space.extend(1.0, 0.0, [1.0, 1.0, 1.0], [0.0, 0.0, 0.0])
    assert space.spin.shape == (2, 3) and space.copy().n == 2
    with pytest.raises(ValueError, match="extend"):
        state.extend([1.0], [0.0], [[1.0, 1.0, 1.0]], [[0.0, 0.0, 0.0]])


# ------------------------------------------------------------------ L1e
def test_l1e_by_hand():
    f, state, fields = hand_case()
    law = make_law("L1e")
    assert law.hypothesis is True and law.id == "L1e"
    re_a, com_a = law.general_acceleration(state, fields)
    assert re_a[0] == pytest.approx([4.0, -6.0])  # g + v x B_g = (7 - 3, 0 - 6)
    assert com_a[0] == pytest.approx([-0.5, 10.0])  # e + v x b = (0 - 0.5, 11 - 1)
    pair = law.forces(state, fields, f)
    assert pair.real[0] == pytest.approx([22.0, -218.0])  # L0: m Re(a) - s^2 q Com(a) = (12, -18) - 20 (-0.5, 10)
    assert pair.total()[0] == pytest.approx([12.0, -18.0])  # lambda = 1: inertia Re(a), the charge has dropped out
    assert law.composer_acceleration(state, fields, f)[0] == pytest.approx([-0.5, 10.0])
    quarter = make_law(LawSpec(reading="L1e", strength=0.25))
    assert quarter.composer_acceleration(state, fields, f)[0] == pytest.approx([-0.125, 2.5])
    assert quarter.forces(state, fields, f).total()[0] == pytest.approx([22.0 - 2.5, -218.0 + 50.0])
    minus = make_law(LawSpec(reading="L1e", sign="-"))
    assert minus.composer_acceleration(state, fields, f)[0] == pytest.approx([0.5, -10.0])


def test_l0_is_the_real_reading_of_mu_a():
    # mathematics: Re(mu a) / Re(mu) is L0's acceleration, for a = E_cal + v x B_cal
    rng = np.random.default_rng(11)
    n, f = 20, Frame.from_degrees(1.7, 70.0)
    state = State(m=rng.uniform(1, 2, n), q=rng.normal(size=n), x=rng.normal(size=(n, 3)), v=rng.normal(size=(n, 3)),
                  fixed=np.zeros(n, bool), alive=np.ones(n, bool))  # fmt: skip
    fields = FieldSample(*(rng.normal(size=(n, 3)) for _ in range(4)))
    re_a, com_a = make_law("L1e").general_acceleration(state, fields)
    real_of_mu_a = state.m[:, None] * re_a - f.s**2 * state.q[:, None] * com_a
    assert np.allclose(real_of_mu_a, make_law("L0").forces(state, fields, f).real, rtol=1e-13, atol=1e-13)


def test_l1e_reduces_to_l0_and_takes_no_composer_option():
    f, state, fields = hand_case()
    reference = make_law("L0").forces(state, fields, f).total()
    for sign in "+-":
        for inertia in ("Re", "Sh", "abs"):
            law = make_law(LawSpec(reading="L1e", strength=0.0, sign=sign, inertia=inertia))
            assert np.array_equal(law.forces(state, fields, f).total(), reference)
            assert not law.composer_acceleration(state, fields, f).any()
            assert np.array_equal(
                law.velocity_coupling(state, fields, f), make_law("L0").velocity_coupling(state, fields, f)
            )
    for option in ({"direction": "torque"}, {"terms": "s q g"}, {"moving": "on"}, {"range": "screened"}):
        with pytest.raises(ValueError, match="does not apply"):
            make_law(LawSpec(reading="L1e", **option))
    # a neutral body moves under L1e exactly as under L0
    neutral = one_body(m=2.0, q=0.0, v=(1.0, 0.0))
    assert np.array_equal(
        make_law("L1e").forces(neutral, fields, f).total(), make_law("L0").forces(neutral, fields, f).total()
    )


def advance(state, law, background, steps=200, dt=0.01, integrator=None):
    ctx = StepContext(law, DirectSum(constants=SCALED, background=background), Frame.scaled())
    integrator = integrator or VelocityVerlet()
    for _ in range(steps):
        state = integrator.step(state, dt, ctx)
    return state


def test_l1e_moves_a_body_in_two_coordinates():
    # uniform g = (0, -2) and e = (3, 0), scaled units (s = 1, 90 deg): constant accelerations, exact for Verlet
    background, t = {"g": [0.0, -2.0], "e": [3.0, 0.0]}, 2.0
    two = advance(one_body(m=1.0, q=1.0), make_law("L1e"), background)
    assert two.x[0] == pytest.approx([0.0, -0.5 * 2.0 * t**2], abs=1e-12)  # Re(a) = g: the charge feels no E in x
    assert two.xc[0] == pytest.approx([0.5 * 3.0 * t**2, 0.0], abs=1e-12)  # Com(a) = e
    assert two.vc[0] == pytest.approx([3.0 * t, 0.0], abs=1e-12)
    # the Real reading of mu X, Re(mu X) / Re(mu) = x - s^2 (q / m) xc, follows L0 (here E = -s^2 e = (-3, 0))
    reference = advance(one_body(m=1.0, q=1.0), make_law("L0"), background)
    assert two.x[0] - two.xc[0] == pytest.approx(reference.x[0], abs=1e-12)
    assert not reference.xc.any() and not reference.vc.any()  # under L0 the Composer coordinate stays at rest
    # a fixed body keeps its Composer coordinate; a Composer velocity given at the start drifts under L0
    pinned = one_body()
    pinned.fixed[0] = True
    assert not advance(pinned, make_law("L1e"), background).xc.any()
    drifting = advance(one_body(vc=[[0.5, -1.0]]), make_law("L0"), background)
    assert drifting.xc[0] == pytest.approx([0.5 * t, -1.0 * t], abs=1e-12) and list(drifting.vc[0]) == [0.5, -1.0]


def test_the_boris_push_with_l1e():
    # a charge moving through uniform b: under L1e its Real velocity is not turned (Re(a) has no b),
    # and its Composer velocity is kicked by v x b; in B_g it turns at Omega = B_g whatever its charge
    t, b = 2.0, 0.5
    in_b = advance(one_body(v=(1.0, 0.0)), make_law("L1e"), {"b": b}, integrator=Boris())
    assert in_b.x[0] == pytest.approx([t, 0.0], abs=1e-12) and in_b.v[0] == pytest.approx([1.0, 0.0], abs=1e-12)
    assert in_b.vc[0] == pytest.approx([0.0, -b * t], abs=1e-12)  # v x b = (v_y b, -v_x b)
    assert in_b.xc[0] == pytest.approx([0.0, -0.5 * b * t**2], abs=1e-12)
    in_bg = advance(
        one_body(v=(1.0, 0.0)), make_law("L1e"), {"B_g": 2.0}, steps=1000, dt=math.pi / 1000, integrator=Boris()
    )
    assert np.linalg.norm(in_bg.x[0]) < 1e-5 and np.linalg.norm(in_bg.v[0]) == pytest.approx(
        1.0, abs=1e-12
    )  # one period
    under_l0 = advance(one_body(v=(1.0, 0.0)), make_law("L0"), {"b": b}, integrator=Boris())
    assert abs(under_l0.v[0, 1]) > 0.5  # under L0 the same charge is turned by b


# ------------------------------------------------------------------ the direction "torque"
def test_torque_by_hand():
    f, state, fields = hand_case()
    state.v[0] = 0.0
    state.radius[0] = 0.2
    law = make_law(LawSpec(reading="L1a", direction="torque"))
    pair = law.forces(state, fields, f)
    assert not pair.composer.any() and np.array_equal(pair.total(), make_law("L0").forces(state, fields, f).total())
    size = math.hypot(70.0, 286.0)  # |s C|, with C = (35, 143) (test_l1_readings.py)
    assert law.torque(state, fields, f)[0] == pytest.approx(0.2 * size)
    assert make_law(LawSpec(reading="L1a", direction="torque", sign="-")).torque(state, fields, f)[0] == pytest.approx(
        -0.2 * size
    )
    assert make_law(LawSpec(reading="L1a", direction="torque", strength=0.0)).torque(state, fields, f)[0] == 0.0
    assert make_law("L1a").torque(state, fields, f) is None and make_law("L0").torque(state, fields, f) is None
    state.radius[0] = 0.0  # a point body gets no torque
    assert law.torque(state, fields, f)[0] == 0.0
    space = one_body(m=3.0, q=5.0, d=3, radius=[0.2])
    fields3 = FieldSample(np.array([[7.0, 0.0, 0.0]]), np.array([[0.0, 11.0, 0.0]]), np.zeros((1, 3)), np.zeros((1, 3)))
    assert law.torque(space, fields3, f)[0] == pytest.approx([0.0, 0.0, 0.2 * size])


def test_torque_spins_a_body_up_without_pushing_it():
    background, t = {"g": [0.0, -2.0], "e": [3.0, 0.0]}, 2.0
    law = make_law(LawSpec(reading="L1a", direction="torque"))
    spun = advance(one_body(m=1.0, q=1.0, radius=[0.5]), law, background)
    reference = advance(one_body(m=1.0, q=1.0), make_law("L0"), background)
    assert np.array_equal(spun.x, reference.x) and np.array_equal(spun.v, reference.v)  # no push: the motion is L0's
    added = np.array([0.0, -2.0]) + np.array([3.0, 0.0])  # s C = q g + m e (s = 1, 90 deg: no charge share)
    assert spun.spin[0] == pytest.approx(0.5 * np.linalg.norm(added) * t, rel=1e-12)  # torque x time
    assert not reference.spin.any()
    pinned = one_body(radius=[0.5])
    pinned.fixed[0] = True
    assert not advance(pinned, law, background).spin.any()


# ------------------------------------------------------------------ settings and the runner
def settings(law, body=None, **numerics):
    return {
        "scenario": "D37",
        "universe": {"units": "scaled", "dimension": 2, "background": {"g": [0.0, -2.0], "e": [3.0, 0.0]}},
        "law": law,
        "bodies": [{"m": 1.0, "q": 1.0, "x": [0.0, 0.0], **(body or {})}],
        "numerics": {"adaptive": False, "dt_initial": 0.01, "steps": 100, "softening": 0.0, **numerics},
        "kind": "mathematics",
    }


def test_a_run_under_l1e_and_under_the_torque(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import validate_results

    result = run(settings({"id": "L1e"}), out_root=tmp_path)
    last = result.timeseries[-1]
    assert last["xc0_0"] == pytest.approx(1.5, abs=1e-12) and last["vc0_0"] == pytest.approx(3.0, abs=1e-12)
    assert result.state.x[0] == pytest.approx([0.0, -1.0], abs=1e-12)
    assert validate_results.validate_folder(result.folder) == []
    spun = run(settings({"id": "L1b", "direction": "torque"}, {"radius": 0.5}), out_root=None)
    assert spun.timeseries[-1]["spin0_0"] == spun.state.spin[0] and "xc0_0" not in spun.timeseries[-1]
    plain = run(settings({"id": "L0"}), out_root=None)
    assert "xc0_0" not in plain.timeseries[-1] and "spin0_0" not in plain.timeseries[-1]
    given = load_settings(settings({"id": "L0"}, {"xc": [1.0, 2.0], "vc": [0.0, 1.0], "spin": 4.0, "radius": 0.1}))
    assert list(given.state.xc[0]) == [1.0, 2.0] and given.state.spin[0] == 4.0 and given.state.radius[0] == 0.1
    assert "xc0_0" in run(settings({"id": "L0"}, {"vc": [0.0, 1.0]}), out_root=None).timeseries[-1]
    with pytest.raises(ValueError, match="does not apply"):
        run(settings({"id": "L1e", "terms": "s q g"}), out_root=None)


@pytest.mark.parametrize(
    "body,message",
    [({"xc": [1.0]}, "xc"), ({"vc": "fast"}, "vc"), ({"spin": [1.0, 2.0]}, "spin"), ({"spin": True}, "spin"),
     ({"radius": -1.0}, "radius"), ({"radius": "big"}, "radius")],
)  # fmt: skip
def test_bad_optional_columns_are_refused(body, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(settings({"id": "L0"}, body))
