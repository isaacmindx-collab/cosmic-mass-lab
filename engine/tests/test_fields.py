"""E2.1, E2.3, E2.4: the direct-sum solver of the static cosmic field.
Formulas cited from the compendium, section "Cosmic Mass", "Cosmic Field Law and law of motion"."""

import time

import numpy as np
import pytest

from cosmicmass.constants import SCALED, SI
from cosmicmass.fields import DirectSum, FieldSample, smallest_separation
from cosmicmass.frame import Frame
from cosmicmass.laws import make_law
from cosmicmass.matter import preset
from cosmicmass.settings import SettingsError, load_settings
from cosmicmass.state import State


def cloud(n, d, seed=4, charges=True):
    rng = np.random.default_rng(seed)
    kinds = [preset(k) for k in ("electron", "proton", "neutron")]
    bodies = [kinds[i] for i in rng.integers(0, 3 if charges else 1, n)]
    return State.from_bodies(bodies, rng.uniform(-1e-9, 1e-9, (n, d)), rng.normal(0, 1e3, (n, d)))


def grid(d, radii=(1e-11, 1e-10, 1e-9, 1e-3, 1.0)):
    rng = np.random.default_rng(0)
    directions = rng.normal(size=(40, d))
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    return np.vstack([r * directions for r in radii])


@pytest.mark.parametrize("d", [2, 3])
def test_T0_5_one_proton_gives_coulomb(d):
    # T0.5: static rho_mu of one proton; the Composer part gives E = -s^2 e = K e / r^2 within 1e-6
    proton, s = preset("proton"), Frame.si().s
    state = State.from_bodies([proton], np.zeros((1, d)))
    points = grid(d)
    field = DirectSum().sample(state, points)
    r = np.linalg.norm(points, axis=1, keepdims=True)
    E = -s * s * field.e
    assert np.allclose(E, SI.K * proton.q * points / r**3, rtol=1e-12, atol=0)  # asked: 1e-6
    assert np.allclose(np.linalg.norm(E, axis=1), SI.K * SI.e / r[:, 0] ** 2, rtol=1e-12, atol=0)
    # and its mass gives Newton's field: g = -G_N M / r^2, towards the source
    assert np.allclose(field.g, -SI.G_N * proton.m * points / r**3, rtol=1e-12, atol=0)
    assert not field.B_g.any() and not field.b.any()  # static part only


def test_one_mass_gives_newton():
    earth = preset("Earth")
    field = DirectSum().sample(State.from_bodies([earth], np.zeros((1, 3))), np.array([[7e6, 0.0, 0.0]]))
    assert field.g[0, 0] == pytest.approx(-SI.G_N * earth.m / 7e6**2, rel=1e-15)
    assert not field.e.any()  # a neutral body has no Composer field


@pytest.mark.parametrize("d", [2, 3])
def test_superposition_and_no_self_field(d):
    state = cloud(30, d)
    solver = DirectSum()
    at_bodies = solver.at_bodies(state)
    for i in range(state.n):  # the field at body i is the sum over the others, one by one
        g, e = np.zeros(d), np.zeros(d)
        for j in range(state.n):
            if j != i:
                r = state.x[i] - state.x[j]
                g -= SI.G_N * state.m[j] * r / np.linalg.norm(r) ** 3
                e -= SI.G_N * state.q[j] * r / np.linalg.norm(r) ** 3
        assert np.allclose(at_bodies.g[i], g, rtol=1e-10, atol=0)
        assert np.allclose(at_bodies.e[i], e, rtol=1e-10, atol=0)
    assert np.all(np.isfinite(at_bodies.g)) and np.all(np.isfinite(at_bodies.e))


def test_internal_forces_under_L0_sum_to_zero():
    # Newton's third law for the whole cloud: the total L0 force vanishes
    state, f = cloud(60, 3), Frame.si()
    force = make_law("L0").forces(state, DirectSum().at_bodies(state), f).total()
    assert np.all(np.abs(force.sum(axis=0)) <= 1e-12 * np.abs(force).sum(axis=0))


def test_absorbed_bodies_are_not_sources_and_fixed_bodies_are():
    state = cloud(10, 2)
    point = np.array([[5e-9, 5e-9]])
    full = DirectSum().sample(state, point)
    state.fixed[3] = True  # a pinned source (setting U6) still acts
    assert np.array_equal(DirectSum().sample(state, point).g, full.g)
    state.alive[3] = False
    without = State.from_bodies([preset("proton")] * 9, np.delete(state.x, 3, axis=0))
    without.m, without.q = np.delete(state.m, 3), np.delete(state.q, 3)
    assert np.allclose(DirectSum().sample(state, point).e, DirectSum().sample(without, point).e, rtol=1e-13)
    assert not np.array_equal(DirectSum().sample(state, point).e, full.e)
    assert np.allclose(DirectSum().at_bodies(state).g[[0, 1, 2, 4]], DirectSum().at_bodies(without).g[:4], rtol=1e-13)
    empty = State.from_bodies([preset("proton")], np.zeros((1, 2)))
    empty.alive[0] = False
    assert not DirectSum().sample(empty, point).g.any() and smallest_separation(empty) == float("inf")


def test_softening_has_the_plummer_form_and_the_D10_length():
    state = State.from_bodies([preset("proton"), preset("electron")], [[0.0, 0.0], [2e-10, 0.0]])
    assert smallest_separation(state) == 2e-10
    solver = DirectSum.with_default_softening(state)
    assert solver.softening == pytest.approx(2e-13)  # D10: 1e-3 of the smallest initial separation
    eps, r = 1e-10, 1e-10
    soft = DirectSum(softening=eps).sample(State.from_bodies([preset("proton")], [[0.0, 0.0]]), np.array([[r, 0.0]]))
    assert soft.g[0, 0] == pytest.approx(-SI.G_N * preset("proton").m * r / (r * r + eps * eps) ** 1.5, rel=1e-14)
    assert np.all(np.isfinite(DirectSum(softening=eps).sample(state, state.x).g))  # finite on a body
    assert DirectSum.with_default_softening(State.from_bodies([preset("proton")], [[0.0, 0.0]])).softening == 0.0
    with pytest.raises(ValueError):
        DirectSum(softening=-1.0)


@pytest.mark.parametrize("d", [2, 3])
def test_uniform_backgrounds_appear_unchanged_at_every_point(d):
    second = [0.0, 0.0, 3.0] if d == 3 else 3.0
    background = {"g": [0.0, -9.81, 0.0][:d], "e": [1e-15, 0.0, 0.0][:d], "B_g": second, "b": second}
    state = cloud(5, d)
    plain, withbg = DirectSum().sample(state, grid(d)), DirectSum(background=background).sample(state, grid(d))
    for key in ("g", "e", "B_g", "b"):
        assert np.allclose(getattr(withbg, key) - getattr(plain, key), background[key], rtol=1e-9, atol=1e-30)
    alone = DirectSum(background={"g": background["g"]}).at_bodies(
        State.from_bodies([preset("neutron")], np.zeros((1, d)))
    )
    assert np.array_equal(alone.g[0], background["g"]) and not alone.e.any()
    with pytest.raises(ValueError):
        DirectSum(background={"wind": [1.0, 0.0]})
    with pytest.raises(ValueError):
        DirectSum(background={"g": [1.0]}).sample(state, grid(d))
    with pytest.raises(ValueError):
        DirectSum().sample(state, np.zeros((3, d + 1)))


def test_scaled_units_use_G_equal_to_one():
    state = State.from_bodies([preset("neutron")], [[0.0, 0.0]])
    state.m[:] = 2.0
    assert DirectSum(constants=SCALED).sample(state, np.array([[2.0, 0.0]])).g[0, 0] == -0.5


def test_blocks_and_speed_for_a_thousand_bodies_in_2D(monkeypatch):
    state = cloud(1000, 2)
    solver = DirectSum.with_default_softening(state)
    start = time.perf_counter()
    whole = solver.at_bodies(state)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.5  # E2.4: one field evaluation under 0.5 s
    monkeypatch.setattr("cosmicmass.fields.direct._BLOCK", 7000)  # force many small blocks
    assert np.allclose(solver.at_bodies(state).g, whole.g, rtol=1e-12, atol=0)
    assert smallest_separation(state) == pytest.approx(solver.softening * 1e3)
    assert isinstance(whole, FieldSample)


def test_settings_accept_backgrounds_and_boundaries():
    base = {"scenario": "x", "bodies": [{"preset": "proton", "x": [0.0, 0.0]}]}
    s = load_settings(
        {
            **base,
            "universe": {
                "background": {"g": [0.0, -9.81], "b": 1e-20},
                "boundary": "reflecting",
                "box": {"lower": [-1, -1], "upper": [1, 1]},
            },
        }
    )
    assert s.universe["background"] == {"g": [0.0, -9.81], "b": 1e-20} and s.universe["boundary"] == "reflecting"
    for bad, named in [
        ({"background": {"g": [1.0]}}, "background.g"),
        ({"background": {"b": [1.0, 0.0]}}, "background.b"),
        ({"background": {"wind": 1}}, "wind"),
        ({"background": "strong"}, "background"),
        ({"boundary": "periodic"}, "boundary"),
        ({"boundary": "absorbing"}, "box"),
    ]:
        with pytest.raises(SettingsError, match=named):
            load_settings({**base, "universe": bad})
