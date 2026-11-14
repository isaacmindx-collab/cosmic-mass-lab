"""E1.3: GNArray agrees with the scalar GeneralNumber, element by element."""

import numpy as np
import pytest

from cosmicmass.frame import Frame
from cosmicmass.gn import GeneralNumber as GN
from cosmicmass.gnarray import GNArray

N = 10_000


def random_pair(frame, seed=20261110):
    rng = np.random.default_rng(seed)
    make = lambda: GNArray(rng.uniform(-5, 5, N), rng.uniform(-5, 5, N) / frame.s, frame)  # noqa: E731
    return make(), make()


def relative_gap(array: GNArray, scalars) -> float:
    """Largest relative difference of either coordinate between an array and a list of scalars."""
    re, com = np.array([z.re for z in scalars]), np.array([z.com for z in scalars])
    with np.errstate(invalid="ignore", divide="ignore"):
        gaps = np.concatenate([np.abs(array.re - re) / np.abs(re), np.abs(array.com - com) / np.abs(com)])
    return float(np.nanmax(gaps))


@pytest.mark.parametrize("deg", [10.14, 79.86, 90.0, 150.0])
@pytest.mark.parametrize("units", ["SI", "scaled"])
def test_agrees_with_the_scalar_class_on_ten_thousand_values(deg, units):
    f = Frame.si(deg) if units == "SI" else Frame.scaled(deg)
    x, y = random_pair(f)
    xs, ys = [x.item(i) for i in range(N)], [y.item(i) for i in range(N)]
    for array, scalars in [
        (x + y, [a + b for a, b in zip(xs, ys)]),
        (x - y, [a - b for a, b in zip(xs, ys)]),
        (x * y, [a * b for a, b in zip(xs, ys)]),
        (x / y, [a / b for a, b in zip(xs, ys)]),
        (x.inverse(), [a.inverse() for a in xs]),
        (x.conjugate(), [a.conjugate() for a in xs]),
    ]:
        assert relative_gap(array, scalars) <= 1e-15
    assert np.array_equal(x.norm_sq(), [a.norm_sq() for a in xs])


def test_scalars_arrays_and_general_numbers_mix():
    f = Frame.from_degrees(2.0, 60.0)
    z = GNArray([1.0, 2.0], [3.0, 4.0], f)
    assert np.all((z + 1 == 1 + z) & (2 * z == z + z) & (z - z == 0) & (1 - z == -(z - 1)))
    assert np.all(np.array([2.0, 3.0]) * z == GNArray([2.0, 6.0], [6.0, 12.0], f))
    g = GN.unit(f)
    assert np.all(z * g == GNArray.from_scalars([z.item(0) * g, z.item(1) * g]))
    assert (z / z).allclose(1.0) and (1 / z).allclose(z.inverse()) and (z / 2).allclose(0.5 * z)
    assert (z * z.inverse()).allclose(GN(1.0, 0.0, f))
    assert not z.allclose(z + 1e-3) and z.allclose(z + 1e-3, abs_tol=1e-2)


def test_vector_fields_broadcast():
    # N numbers times an (N, d) vector field, as in mu * E_cal
    f = Frame.si()
    mu = GNArray([1.0, 2.0, 3.0], [1e-10, 0.0, -1e-10], f)
    field = GNArray(np.arange(6.0).reshape(3, 2), np.ones((3, 2)) * 1e-10, f)
    force = mu[:, None] * field
    assert force.shape == (3, 2) and len(force) == 3
    for i in range(3):
        for k in range(2):
            assert force.item(i, k) == mu.item(i) * field.item(i, k)
    assert GNArray(1.0, [1.0, 2.0], f).shape == (2,) and GNArray.zeros((4, 3), f).shape == (4, 3)


def test_refusals():
    f, g = Frame.from_degrees(1.0, 60.0), Frame.from_degrees(1.0, 90.0)
    z = GNArray([1.0], [1.0], f)
    for op in (
        lambda: z + GNArray([1.0], [1.0], g),
        lambda: z * GN(1.0, 1.0, g),
        lambda: z - GNArray([1.0], [1.0], g),
        lambda: z / GN(1.0, 1.0, g),
        lambda: GNArray.from_scalars([GN(1.0, 1.0, f), GN(1.0, 1.0, g)]),
    ):
        with pytest.raises(ValueError):
            op()
    for op in (lambda: z + "1", lambda: z * True, lambda: z - "1", lambda: z / "1", lambda: z.allclose("1")):
        with pytest.raises(TypeError):
            op()
    with pytest.raises(ZeroDivisionError):
        GNArray([0.0, 1.0], [0.0, 1.0], f).inverse()
    import mpmath

    with pytest.raises(TypeError):
        GNArray([1.0], [1.0], Frame.from_degrees(mpmath.mpf(1), 60))
    assert (z == GNArray([1.0], [1.0], g)) is False and (z != "1") and "GNArray(shape=(1,)" in repr(z)
