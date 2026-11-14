"""E1.2: GeneralNumber. Formulas cited from the compendium (docs/formulas-compendium/),
section "General Numbers"."""

import math
import random

import mpmath
import pytest

from cosmicmass.frame import Frame
from cosmicmass.gn import GeneralNumber as GN

ANGLES = [10.14, 45.0, 79.86, 90.0, 120.0, 170.0]


def frames():
    return [Frame.from_degrees(s, deg) for deg in ANGLES for s in (1.0, 1.16043, Frame.si().s)]


def bridge(z: GN) -> complex:
    """ "Turning Unit and the bridge to C": z -> Sh z + i Ht z is an isomorphism of
    fields onto C, with Sh z = a + b s cos(phi_bar) and Ht z = b s sin(phi_bar)."""
    f = z.frame
    return complex(z.re + z.com * f.s * f.cos_phi(), z.com * f.s * f.sin_phi())


def sample(rng, frame, n=200):
    # Composer coordinates are scaled by 1/s so that both coordinates matter
    return [GN(rng.uniform(-5, 5), rng.uniform(-5, 5) / frame.s, frame) for _ in range(n)]


def test_rule_of_the_square_exact_at_50_digits():
    # "Rule of the Square and the product": G^2 = 2 s cos(phi_bar) G - s^2
    with mpmath.workdps(50):
        for deg in ANGLES:
            for s in ("1", "1.16043", "11604270426.53138"):
                f = Frame.from_degrees(mpmath.mpf(s), deg)
                G = GN.unit(f)
                assert G * G == 2 * f.s * mpmath.cos(f.phi_bar) * G - f.s**2
                assert (G * G).re == -(mpmath.mpf(s) ** 2)


def test_product_formula_term_by_term():
    # (a + bG)(c + dG) = (ac - s^2 bd) + (ad + bc + 2 s cos(phi_bar) bd) G
    f = Frame.from_degrees(3.0, 60.0)
    z = GN(2.0, 5.0, f) * GN(7.0, 11.0, f)
    assert z.re == 2 * 7 - 9 * 5 * 11
    assert z.com == pytest.approx(2 * 11 + 5 * 7 + 2 * 3 * 0.5 * 5 * 11, rel=1e-15)


def test_inverse_exact_at_50_digits():
    # "Conjugate, skew flip, division": 1/z = conj(z) / |z|^2, so z * (1/z) = 1
    with mpmath.workdps(50):
        f = Frame.from_degrees(mpmath.mpf("1.16043"), mpmath.mpf("79.86"))
        z = GN(mpmath.mpf("2.5"), mpmath.mpf("-0.75"), f)
        assert (z * z.inverse()).isclose(1, rel_tol=1e-48)
        assert isinstance(z.inverse().re, mpmath.mpf)


def test_x_times_inverse_is_one():
    rng = random.Random(20261110)
    for f in frames():
        for z in sample(rng, f):
            assert (z * z.inverse()).isclose(1, rel_tol=1e-12)
            assert (z / z).isclose(1, rel_tol=1e-12)


def test_product_and_division_agree_with_the_bridge_to_C():
    # an independent check: the product in the leaning frame is the complex product
    rng = random.Random(1)
    for f in frames():
        zs, ws = sample(rng, f, 50), sample(rng, f, 50)
        for z, w in zip(zs, ws):
            assert bridge(z * w) == pytest.approx(bridge(z) * bridge(w), rel=1e-12)
            assert bridge(z / w) == pytest.approx(bridge(z) / bridge(w), rel=1e-11)
            assert bridge(z + w) == pytest.approx(bridge(z) + bridge(w), rel=1e-12, abs=1e-12)


def test_conjugate_and_length():
    # conj(z) = (a + 2b s cos) - bG ; z conj(z) = |z|^2 ; the norm is multiplicative
    rng = random.Random(2)
    for f in frames():
        zs = sample(rng, f, 20)
        for z, w in zip(zs, reversed(zs)):
            assert (z * z.conjugate()).isclose(z.norm_sq(), rel_tol=1e-12)
            assert z.norm_sq() == pytest.approx(abs(bridge(z)) ** 2, rel=1e-12)
            assert (z * w).norm_sq() == pytest.approx(z.norm_sq() * w.norm_sq(), rel=1e-11)
            assert z.conjugate().conjugate().isclose(z)


def test_field_laws_on_random_values():
    rng = random.Random(3)
    f = Frame.si()
    for x, y, z in zip(sample(rng, f, 50), sample(rng, f, 50), sample(rng, f, 50)):
        assert x + y == y + x and x * y == y * x
        assert ((x * y) * z).isclose(x * (y * z), rel_tol=1e-12)
        assert (x * (y + z)).isclose(x * y + x * z, rel_tol=1e-11, abs_tol=1e-11)
        assert x - x == 0 and x + (-x) == 0


def test_real_scalars_mix_with_general_numbers():
    f = Frame.from_degrees(2.0, 79.86)
    z = GN(3.0, 4.0, f)
    assert z + 1 == 1 + z == GN(4.0, 4.0, f)
    assert z - 1 == GN(2.0, 4.0, f) and 1 - z == GN(-2.0, -4.0, f)
    assert 2 * z == z * 2 == GN(6.0, 8.0, f) and z / 2 == GN(1.5, 2.0, f)
    assert (1 / z).isclose(z.inverse())
    assert GN(5.0, 0.0, f) == 5 and z != 3.0 and z.add(1) == z + 1 and z.mul(2) == 2 * z


def test_real_part_of_the_product_does_not_depend_on_the_angle():
    # "Cosmic Interaction Law and its reading": Re[(a+bG)(c+dG)] = ac - s^2 bd at every angle
    s = Frame.si().s
    reals = {
        (GN(2.0, 3e-10, f) * GN(5.0, -7e-10, f)).re for f in (Frame.from_degrees(s, deg) for deg in range(10, 171, 5))
    }
    assert reals == {2.0 * 5.0 - s * s * 3e-10 * -7e-10}


def test_frames_must_match():
    z, w = GN(1.0, 1.0, Frame.from_degrees(1.0, 60.0)), GN(1.0, 1.0, Frame.from_degrees(1.0, 90.0))
    for op in (lambda: z + w, lambda: z * w, lambda: z / w, lambda: z - w, lambda: z.isclose(w)):
        with pytest.raises(ValueError):
            op()
    assert z != w


def test_zero_has_no_inverse_and_unknown_types_are_refused():
    f = Frame.scaled()
    with pytest.raises(ZeroDivisionError):
        GN(0.0, 0.0, f).inverse()
    with pytest.raises(TypeError):
        GN(1.0, 0.0, f) + "1"
    with pytest.raises(TypeError):
        GN(1.0, 0.0, f) * "1"
    with pytest.raises(TypeError):
        GN(1.0, 0.0, f).isclose("1")
    assert GN(1.0, 0.0, f) != "1" and not math.isnan(GN(1.0, 2.0, f).norm_sq())
    assert hash(GN(1.0, 2.0, f)) == hash(GN(1.0, 2.0, f)) and "GeneralNumber(1.0, 2.0" in repr(GN(1.0, 2.0, f))
