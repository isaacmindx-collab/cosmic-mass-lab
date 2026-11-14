"""E4.3 (L1b, L1c, L1d) and E3.4 (L7 inertia): readings of the Composer coordinate, hypotheses (D1).
Rule (labelled, `laws/l1.py`): force = L0 + lambda x what the reading adds. Hand-computed cases."""

import math

import numpy as np
import pytest

from cosmicmass import readings
from cosmicmass.fields import FieldSample
from cosmicmass.frame import Frame
from cosmicmass.laws import LawSpec, available_laws, make_law
from cosmicmass.state import State

READINGS = ("L1a", "L1b", "L1c", "L1d")
TERMS = ("all", "s q g", "-m E/s", "-2 cos q E")


def hand_case():
    """One body m = 3, q = 5 in the frame s = 2, phi_bar = 60 deg, with g = (7, 0) and e = (0, 11).
    Re(mu E_cal) = m g - s^2 q e = (21, -220); Com(mu E_cal) = q g + m e + 2 s cos q e = (35, 143)."""
    f = Frame.from_degrees(2.0, 60.0)
    state = State(m=[3.0], q=[5.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True])
    fields = FieldSample(np.array([[7.0, 0.0]]), np.array([[0.0, 11.0]]), np.zeros(1), np.zeros(1))
    return f, state, fields


def random_case(d, seed=5, n=25):
    rng = np.random.default_rng(seed)
    f = Frame.from_degrees(1.7, 70.0)
    second = (n, 3) if d == 3 else (n,)
    fields = FieldSample(
        rng.normal(size=(n, d)), rng.normal(size=(n, d)), rng.normal(size=second), rng.normal(size=second)
    )
    state = State(
        m=rng.uniform(1, 2, n),
        q=rng.normal(size=n),
        x=rng.normal(size=(n, d)),
        v=rng.normal(size=(n, d)),
        fixed=np.zeros(n, bool),
        alive=np.ones(n, bool),
    )
    return f, state, fields


def test_the_readings_are_registered_hypotheses():
    assert set(READINGS) <= set(available_laws())
    for reading in READINGS:
        law = make_law(reading)
        assert law.hypothesis is True and law.id == reading
        assert make_law(LawSpec(reading=reading, direction="torque")).spec.direction == "torque"  # D37


def test_the_readings_by_hand():
    f, state, fields = hand_case()
    added = lambda reading, **kw: make_law(LawSpec(reading=reading, **kw)).forces(state, fields, f).composer[0]  # noqa: E731
    real = np.array([21.0, -220.0])
    c = np.array([35.0, 143.0])
    assert make_law("L0").forces(state, fields, f).real[0] == pytest.approx(real)
    assert added("L1a") == pytest.approx(2 * c)  # s C
    assert added("L1b") == pytest.approx(2 * 0.5 * c)  # s cos C
    assert added("L1c") == pytest.approx(2 * math.sqrt(3) / 2 * c)  # s sin C
    # L1d: the length of the vector mu E_cal along its shadow; the force is that, as L0 + the addition
    shadow, height = real + 2 * 0.5 * c, 2 * math.sqrt(3) / 2 * c
    length = math.sqrt(shadow @ shadow + height @ height)
    total = make_law("L1d").forces(state, fields, f).total()[0]
    assert total == pytest.approx(length * shadow / np.linalg.norm(shadow))
    assert np.linalg.norm(total) == pytest.approx(math.sqrt(74087.0))  # 56^2 + 77^2 + 3 (35^2 + 143^2)
    # sign and strength scale what is added; the Real part (L0) stays
    assert added("L1b", sign="-", strength=0.5) == pytest.approx(-0.5 * c)
    assert added("L1c", strength="cos_phi_bar") == pytest.approx(0.5 * math.sqrt(3) * c)


def test_l1d_leaves_a_body_alone_when_its_composer_coordinate_is_zero():
    # a neutral mass in gravity: C = 0, so |mu E_cal| along its shadow is L0's force itself
    f = Frame.si()
    state = State(m=[2.0], q=[0.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True])
    fields = FieldSample(np.array([[0.0, -9.8]]), np.zeros((1, 2)), np.zeros(1), np.zeros(1))
    pair = make_law("L1d").forces(state, fields, f)
    assert np.array_equal(pair.real, [[0.0, -19.6]]) and np.allclose(pair.composer, 0.0, atol=1e-15)
    # no field at all: no force, and no division by zero
    empty = FieldSample(np.zeros((1, 2)), np.zeros((1, 2)), np.zeros(1), np.zeros(1))
    assert np.array_equal(make_law("L1d").forces(state, empty, f).total(), [[0.0, 0.0]])
    # a shadow of zero length: the direction of the Composer terms is used
    state = State(m=[1.0], q=[1.0], x=[[0.0, 0.0]], v=[[0.0, 0.0]], fixed=[False], alive=[True])
    f90 = Frame.from_degrees(1.0, 90.0)  # Sh = Re when cos = 0; Re = m g - q e = 0 with g = e
    fields = FieldSample(np.array([[1.0, 0.0]]), np.array([[1.0, 0.0]]), np.zeros(1), np.zeros(1))
    total = make_law("L1d").forces(state, fields, f90).total()[0]
    assert total == pytest.approx([2.0, 0.0])  # C = q g + m e = (2, 0); |A| = |Ht| = 2, along C


@pytest.mark.parametrize("d", [2, 3])
def test_every_reading_reduces_to_l0_exactly(d):
    # the reduce-to-L0 test (ARCHITECTURE.md, section 7): strength 0 gives L0's forces, bit for bit
    f, state, fields = random_case(d)
    reference = make_law("L0").forces(state, fields, f).total()
    for reading in READINGS:
        for terms in TERMS:
            for sign in "+-":
                for inertia in ("Re", "Sh", "abs"):
                    spec = LawSpec(reading=reading, strength=0.0, terms=terms, sign=sign, inertia=inertia)
                    assert np.array_equal(make_law(spec).forces(state, fields, f).total(), reference), spec


def test_the_angle_in_the_readings():
    f60, state, fields = random_case(2)
    at = lambda reading, deg: make_law(reading).forces(state, fields, Frame.from_degrees(1.7, deg)).composer  # noqa: E731
    assert np.allclose(at("L1b", 90.0), 0.0, atol=1e-12)  # the shadow adds nothing at 90 deg
    c = make_law("L1a").composer_coordinate(state, fields, Frame.from_degrees(1.7, 90.0))
    assert np.allclose(at("L1c", 90.0), 1.7 * c, rtol=1e-12)  # the height is all of s C at 90 deg


def test_l7_inertia_readings():
    f = Frame.from_degrees(2.0, 60.0)
    state = State(m=[3.0, 1.0], q=[5.0, -0.5], x=[[0.0, 0.0], [1.0, 0.0]], v=[[0.0, 0.0]] * 2, fixed=[False] * 2,
                  alive=[True] * 2)  # fmt: skip
    mu = state.mu(f)
    law = lambda inertia: make_law(LawSpec(reading="L1b", inertia=inertia))  # noqa: E731
    assert law("Re").inertia(state, f) == pytest.approx([3.0, 1.0])
    assert law("Sh").inertia(state, f) == pytest.approx([3.0 + 5.0 * 2 * 0.5, 1.0 - 0.5 * 2 * 0.5])  # m + q s cos
    assert law("abs").inertia(state, f) == pytest.approx(readings.abs(mu))
    assert law("abs").inertia(state, f)[0] == pytest.approx(math.sqrt(8.0**2 + (5.0 * 2 * math.sqrt(3) / 2) ** 2))
    with pytest.raises(ValueError):
        make_law(LawSpec(reading="L0", inertia="Sh"))  # the reference law takes no option


def moving_case():
    """The hand case of `hand_case`, moving with v = (2, -1), in uniform B_g = 3 and b = 0.5 (2D)."""
    f, state, fields = hand_case()
    state.v[0] = [2.0, -1.0]
    fields = FieldSample(fields.g, fields.e, np.array([3.0]), np.array([0.5]))
    return f, state, fields


def test_l6_the_moving_body_term_by_hand():
    f, state, fields = moving_case()
    vxb, vxbg = np.array([-1.0 * 0.5, -2.0 * 0.5]), np.array([-1.0 * 3.0, -2.0 * 3.0])  # (v_y B, -v_x B)
    moving = 3.0 * vxb + 5.0 * vxbg + 2 * 2 * 0.5 * 5.0 * vxb  # m (v x b) + q (v x B_g) + 2 s cos q (v x b)
    c = np.array([35.0, 143.0])
    added = lambda **kw: make_law(LawSpec(reading="L1a", **kw)).forces(state, fields, f).composer[0]  # noqa: E731
    assert added() == pytest.approx(2 * c)  # L6 off: as before
    assert added(moving="on") == pytest.approx(2 * (c + moving))
    assert added(moving="only") == pytest.approx(2 * moving)
    assert added(moving="on", terms="s q g") == pytest.approx(2 * (np.array([35.0, 0.0]) + moving))
    # L1d reads the Real part of the same product: with "only", Re(mu (v x B_cal)) = m v x B_g - s^2 q v x b
    real = 3.0 * vxbg - 4.0 * 5.0 * vxb
    shadow, height = real + 1.0 * moving, math.sqrt(3) * moving
    total = make_law(LawSpec(reading="L1d", moving="only")).forces(state, fields, f).composer[0]
    expected = math.sqrt(shadow @ shadow + height @ height) * shadow / np.linalg.norm(shadow) - real
    assert total == pytest.approx(expected)


@pytest.mark.parametrize("d", [2, 3])
def test_l4_directions(d):
    f, state, fields = random_case(d)
    radial = make_law("L1a").forces(state, fields, f).composer
    perpendicular = make_law(LawSpec(reading="L1a", direction="perpendicular")).forces(state, fields, f).composer
    assert np.allclose(perpendicular[:, 0], -radial[:, 1]) and np.allclose(perpendicular[:, 1], radial[:, 0])
    if d == 3:
        assert np.array_equal(perpendicular[:, 2], radial[:, 2])  # a turn about z keeps z
    assert np.allclose(np.sum(perpendicular[:, :2] * radial[:, :2], axis=1), 0.0, atol=1e-12)
    along = make_law(LawSpec(reading="L1a", direction="velocity")).forces(state, fields, f).composer
    unit = state.v / np.linalg.norm(state.v, axis=1)[:, None]
    assert np.allclose(along, np.linalg.norm(radial, axis=1)[:, None] * unit, rtol=1e-12)
    state.v[0] = 0.0  # a body at rest gets nothing along its velocity
    along = make_law(LawSpec(reading="L1a", direction="velocity")).forces(state, fields, f).composer
    assert np.array_equal(along[0], np.zeros(d))


@pytest.mark.parametrize("d", [2, 3])
def test_every_option_reduces_to_l0_exactly(d):
    # the reduce-to-L0 test over the options added in part B: directions and the moving-body term
    f, state, fields = random_case(d)
    reference = make_law("L0").forces(state, fields, f).total()
    for reading in READINGS:
        for direction in ("radial", "perpendicular", "velocity"):
            for moving in ("off", "on", "only"):
                spec = LawSpec(reading=reading, strength=0.0, direction=direction, moving=moving)
                assert np.array_equal(make_law(spec).forces(state, fields, f).total(), reference), spec
