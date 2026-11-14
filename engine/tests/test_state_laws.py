"""E5.1, E4.1, E4.2: the state, the law interface and the reference law L0.
Formulas cited from the compendium, section "Cosmic Mass"."""

import json

import numpy as np
import pytest

from cosmicmass.constants import SI
from cosmicmass.fields import FieldSample
from cosmicmass.frame import Frame
from cosmicmass.laws import ForcePair, Law, LawSpec, available_laws, make_law
from cosmicmass.laws.base import register
from cosmicmass.laws.l0 import L0, cross
from cosmicmass.matter import PRESETS, preset
from cosmicmass.state import State


def field_of_a_source_at_rest(source, x_source, points, frame) -> FieldSample:
    """ "Cosmic Field Law and law of motion": the field of a source at rest is
    E_cal = -G mu_s e_r / r^2, so g = -G m_s e_r / r^2 and e = -G q_s e_r / r^2."""
    r = points - x_source
    dist = np.linalg.norm(r, axis=1, keepdims=True)
    e_r = r / dist
    zeros = FieldSample.zeros(len(points), points.shape[1])
    g, e = -SI.G_N * source.m * e_r / dist**2, -SI.G_N * source.q * e_r / dist**2
    return FieldSample(g, e, zeros.B_g, zeros.b)


# ---------------------------------------------------------------- state (E5.1)
def two_bodies(d=2):
    x = np.zeros((2, d))
    x[1, 0] = 1e-10
    return State.from_bodies([preset("proton"), preset("electron")], x)


def test_state_shapes_and_cosmic_masses():
    s = two_bodies(3)
    f = Frame.si()
    assert (s.n, s.dimension, s.t) == (2, 3, 0.0) and not s.v.any() and s.alive.all() and not s.fixed.any()
    assert np.array_equal(s.mu(f).re, s.m) and np.array_equal(s.mu(f).com, s.q)


def test_absorbed_bodies_are_switched_off_never_deleted_and_totals_survive_a_copy():
    f = Frame.si()
    s = two_bodies()
    before = s.total_mu(f)
    c = s.copy()
    assert np.all(c.total_mu(f) == before)
    c.alive[1] = False  # absorb the electron in the copy
    c.x[0, 0] = 5.0
    assert c.n == 2 and np.all(c.total_mu(f) == before)  # still counted
    assert c.total_mu(f, alive_only=True).item() == preset("proton").mu(f)
    assert s.alive.all() and s.x[0, 0] == 0.0  # the original is untouched


@pytest.mark.parametrize(
    "bad",
    [
        dict(m=[1.0], q=[0.0, 0.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True]),
        dict(m=[1.0], q=[0.0], x=[[0.0, 0.0]], v=[[0.0, 0.0, 0.0]], fixed=[False], alive=[True]),
        dict(m=[1.0], q=[0.0], x=[[0.0]], v=[[0.0]], fixed=[False], alive=[True]),
        dict(m=[float("nan")], q=[0.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True]),
        dict(m=[[1.0]], q=[0.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True]),
    ],
)
def test_state_refuses_inconsistent_arrays(bad):
    with pytest.raises(ValueError):
        State(**bad)


# ------------------------------------------------------- law interface (E4.1)
def test_lawspec_round_trips_through_json():
    spec = LawSpec(
        reading="L1a",
        sign="-",
        strength=1e-12,
        direction="perpendicular",
        terms="s q g",
        moving="on",
        inertia="Sh",
        range="screened",
    )
    assert LawSpec.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec
    assert LawSpec.from_dict(json.loads(json.dumps(LawSpec().to_dict()))) == LawSpec()
    # the stamp keys of team/RESULTS-STANDARD.md, section 2
    assert set(LawSpec().to_dict()) == {"id", "sign", "lambda", "direction", "terms", "B_cal", "inertia", "range"}
    assert LawSpec.from_dict({"id": "L1a", "lambda": "cos_phi_bar"}).strength == "cos_phi_bar"


@pytest.mark.parametrize(
    "bad",
    [
        {"id": "L9"},
        {"sign": "x"},
        {"lambda": "big"},
        {"lambda": float("inf")},
        {"lambda": True},
        {"direction": "up"},
        {"colour": "red"},
        {"inertia": "Com"},
    ],
)
def test_unknown_law_options_are_refused(bad):
    with pytest.raises(ValueError):
        LawSpec.from_dict(bad)


def test_registry_of_laws():
    assert "L0" in available_laws()
    law = make_law("L0")
    assert isinstance(law, L0) and isinstance(law, Law) and law.id == "L0" and law.spec == LawSpec()
    assert L0.hypothesis is False and Law.hypothesis is True  # only L0 is not a hypothesis (D1)
    with pytest.raises(NotImplementedError):
        make_law(LawSpec(reading="L1e"))
    with pytest.raises(ValueError):
        make_law(LawSpec(reading="L0", sign="-"))  # the reference law takes no option
    with pytest.raises(ValueError):
        L0(LawSpec(reading="L1a"))
    with pytest.raises(ValueError):
        register(L0)
    with pytest.raises(NotImplementedError):
        Law.forces(law, None, None, None)

    class Other(Law):
        reading = "L1a"

    with pytest.raises(NotImplementedError):
        Other(LawSpec(reading="L1a", inertia="abs")).inertia(two_bodies(), Frame.si())


# ----------------------------------------------------------------- L0 (E4.2)
@pytest.mark.parametrize("d", [2, 3])
@pytest.mark.parametrize("deg", [10.0, 79.86, 90.0, 170.0])
def test_two_bodies_feel_newton_plus_coulomb(d, deg):
    # "Cosmic Interaction Law and its reading": F = (G m m' - K q q') / r^2, attractive when positive
    f = Frame.si(deg)
    law = make_law("L0")
    r = 1e-10
    for a in PRESETS.values():
        for b in PRESETS.values():
            x = np.zeros((2, d))
            x[1, 0] = r
            state = State.from_bodies([a, b], x)
            on_a = field_of_a_source_at_rest(b, x[1], x[:1], f)
            on_b = field_of_a_source_at_rest(a, x[0], x[1:], f)
            pair = law.forces(
                state,
                FieldSample(
                    np.vstack([on_a.g, on_b.g]),
                    np.vstack([on_a.e, on_b.e]),
                    np.concatenate([on_a.B_g, on_b.B_g]),
                    np.concatenate([on_a.b, on_b.b]),
                ),
                f,
            )
            assert isinstance(pair, ForcePair) and not pair.composer.any()
            expected = (SI.G_N * a.m * b.m - SI.K * a.q * b.q) / r**2
            force = pair.total()
            assert force[0, 0] == pytest.approx(expected, rel=1e-15, abs=0)  # a is pulled towards +x
            assert force[1, 0] == pytest.approx(-expected, rel=1e-15, abs=0)  # Newton's third law
            assert not force[:, 1:].any()


def test_l0_force_is_the_same_at_every_frame_angle():
    x = np.array([[0.0, 0.0], [3e-11, 4e-11]])
    state = State.from_bodies([preset("proton"), preset("electron")], x, v=[[1e3, -2e3], [5e5, 1e5]])
    forces = []
    for deg in range(10, 171, 5):
        f = Frame.si(deg)
        fields = field_of_a_source_at_rest(preset("alpha"), np.array([1e-10, -1e-10]), x, f)
        forces.append(make_law("L0").forces(state, fields, f).total())
    assert all(np.array_equal(forces[0], other) for other in forces[1:])


def test_l0_is_newton_and_lorentz_with_the_second_field():
    # m dv/dt = m (g + v x B_g) + q (E + v x B), with E = -s^2 e and B = -s^2 b
    f = Frame.si()
    rng = np.random.default_rng(11)
    n, s = 40, f.s
    for d in (2, 3):
        second = (n, 3) if d == 3 else (n,)
        fields = FieldSample(
            rng.normal(size=(n, d)), rng.normal(size=(n, d)) / s, rng.normal(size=second), rng.normal(size=second) / s
        )
        state = State(
            m=rng.uniform(1, 2, n),
            q=rng.normal(size=n) / s,
            x=rng.normal(size=(n, d)),
            v=rng.normal(size=(n, d)),
            fixed=np.zeros(n, bool),
            alive=np.ones(n, bool),
        )
        E, B = -s * s * fields.e, -s * s * fields.b
        m, q = state.m[:, None], state.q[:, None]
        expected = m * (fields.g + cross(state.v, fields.B_g)) + q * (E + cross(state.v, B))
        law = make_law("L0")
        assert np.allclose(law.forces(state, fields, f).total(), expected, rtol=1e-12, atol=1e-12)
        assert np.array_equal(law.inertia(state, f), state.m)  # inertia Re(mu) = m
    v2 = np.array([[2.0, 3.0]])
    assert np.array_equal(cross(v2, np.array([5.0])), [[15.0, -10.0]])  # (v_y B, -v_x B)


def test_field_sample_shapes_and_superposition():
    a, f = FieldSample.zeros(4, 3), Frame.si()
    assert a.E_cal(f).shape == (4, 3) and a.B_cal(f).shape == (4, 3) and FieldSample.zeros(4, 2).b.shape == (4,)
    ones = FieldSample(np.ones((4, 3)), np.ones((4, 3)), np.ones((4, 3)), np.ones((4, 3)))
    assert np.array_equal((ones + ones).g, 2 * np.ones((4, 3))) and np.array_equal((ones + ones).b, 2 * np.ones((4, 3)))
    for bad in (
        lambda: FieldSample(np.ones((4, 3)), np.ones((4, 2)), np.ones((4, 3)), np.ones((4, 3))),
        lambda: FieldSample(np.ones((4, 2)), np.ones((4, 2)), np.ones((4, 3)), np.ones((4,))),
        lambda: FieldSample(np.ones(4), np.ones(4), np.ones(4), np.ones(4)),
    ):
        with pytest.raises(ValueError):
            bad()
