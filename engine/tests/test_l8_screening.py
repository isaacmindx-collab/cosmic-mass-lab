"""E4.4, option L8: the Composer coupling screened over the Debye length of the population.
Labelled choices in `laws/l1.py` and `fields/direct.py`; checks against the formulas."""

import math

import numpy as np
import pytest

from cosmicmass.constants import SCALED, SI
from cosmicmass.fields import DirectSum, FieldSample
from cosmicmass.fields.direct import debye_length
from cosmicmass.frame import Frame
from cosmicmass.integrators import StepContext
from cosmicmass.laws import LawSpec, make_law
from cosmicmass.state import State


def plasma(d=3, n=40, seed=3):
    rng = np.random.default_rng(seed)
    return State(
        m=np.ones(n),
        q=np.where(np.arange(n) % 2 == 0, 1.0, -1.0),
        x=rng.uniform(0.0, 10.0, (n, d)),
        v=rng.normal(size=(n, d)),
        fixed=np.zeros(n, bool),
        alive=np.ones(n, bool),
    )


def test_debye_length_by_hand():
    state = plasma(3)
    kinetic2 = float(np.sum(state.m * np.sum(state.v**2, axis=1)))
    temperature = kinetic2 / (3 * state.n)  # k_B = 1 in scaled units
    volume = float(np.prod(np.ptp(state.x, axis=0)))
    expected = math.sqrt(temperature * volume / (4 * math.pi * 1.0 * state.n))  # sum q^2 = n
    assert debye_length(state, SCALED, 1.0) == pytest.approx(expected, rel=1e-14)
    flat = plasma(2)
    area = float(np.prod(np.ptp(flat.x, axis=0)))
    t2 = float(np.sum(flat.m * np.sum(flat.v**2, axis=1))) / (2 * flat.n)
    expected2 = math.sqrt(t2 * area * math.sqrt(area / flat.n) / (4 * math.pi * flat.n))
    assert debye_length(flat, SCALED, 1.0) == pytest.approx(expected2, rel=1e-14)
    # no temperature, no charge, or a single body: no screening
    cold = plasma(3)
    cold.v[:] = 0.0
    neutral = plasma(3)
    neutral.q[:] = 0.0
    one = plasma(3, n=1)
    pinned = plasma(3)
    pinned.fixed[:] = True
    for state in (cold, neutral, one, pinned):
        assert debye_length(state, SCALED, 1.0) == math.inf


def test_the_screened_kernel_of_two_bodies():
    state = State(m=[2.0, 1.0], q=[3.0, 0.0], x=[[0.0, 0.0], [4.0, 0.0]], v=[[0.0, 0.0]] * 2, fixed=[False] * 2,
                  alive=[True] * 2)  # fmt: skip
    solver, length = DirectSum(constants=SCALED, background={"g": [0.0, 1.0]}), 2.5
    plain, screened = solver.at_bodies(state), solver.at_bodies_screened(state, length)
    factor = math.exp(-4.0 / length) * (1 + 4.0 / length)
    assert screened.g[1, 0] == pytest.approx(factor * plain.g[1, 0], rel=1e-14)  # -G m / r^2, screened
    assert screened.e[1, 0] == pytest.approx(factor * plain.e[1, 0], rel=1e-14)
    assert screened.g[1, 1] == plain.g[1, 1] == 1.0  # the uniform background is not screened
    assert np.array_equal(solver.at_bodies_screened(state, math.inf).g, plain.g)


def test_l8_screens_the_composer_coupling_and_not_l0():
    state, frame = plasma(3), Frame.scaled()
    solver = DirectSum(constants=SCALED)
    length = debye_length(state, SCALED, 1.0)
    screened = StepContext(make_law(LawSpec(reading="L1a", range="screened")), solver, frame)
    plain = StepContext(make_law("L1a"), solver, frame)
    a_screened, a_plain = screened.acceleration(state), plain.acceleration(state)
    # the Composer part follows the screened field; the Real part (L0) is the same
    fields = solver.at_bodies(state)
    with_screened = FieldSample(
        fields.g, fields.e, fields.B_g, fields.b, screened=solver.at_bodies_screened(state, length)
    )
    pair = make_law(LawSpec(reading="L1a", range="screened")).forces(state, with_screened, frame)
    screened_field = with_screened.screened
    c = state.q[:, None] * screened_field.g + state.m[:, None] * screened_field.e  # 90 deg: no charge share
    assert np.allclose(pair.composer, c, rtol=1e-12, atol=1e-15)  # s = 1, lambda = 1: s C of the screened field
    assert np.array_equal(pair.real, make_law("L0").forces(state, fields, frame).real)  # L0 is never screened
    assert np.allclose(a_screened - a_plain, pair.composer - make_law("L1a").forces(state, fields, frame).composer)
    assert not np.allclose(a_screened, a_plain)
    # strength 0: L0 exactly, screened or not (the reduce-to-L0 test)
    zero = StepContext(make_law(LawSpec(reading="L1a", range="screened", strength=0.0)), solver, frame)
    assert np.array_equal(zero.acceleration(state), StepContext(make_law("L0"), solver, frame).acceleration(state))
    # a cold population is not screened: the same forces as 1/r^2
    state.v[:] = 0.0
    assert np.array_equal(
        StepContext(make_law(LawSpec(reading="L1a", range="screened")), solver, frame).acceleration(state),
        StepContext(make_law("L1a"), solver, frame).acceleration(state),
    )


def test_l8_needs_the_screened_field():
    state = plasma(2)
    fields = DirectSum(constants=SI).at_bodies(state)
    with pytest.raises(ValueError, match="screened"):
        make_law(LawSpec(reading="L1b", range="screened")).forces(state, fields, Frame.si())
