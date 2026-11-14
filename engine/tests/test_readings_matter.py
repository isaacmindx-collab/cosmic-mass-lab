"""E1.4 and E1.5: the readings and the matter presets. Formulas cited from the compendium,
section "General Numbers", and from ARCHITECTURE.md, section 5."""

import math

import mpmath
import numpy as np
import pytest

from cosmicmass import readings as R
from cosmicmass.frame import Frame
from cosmicmass.gn import GeneralNumber as GN
from cosmicmass.gnarray import GNArray
from cosmicmass.matter import PRESETS, CosmicMass, preset

FRAMES = [Frame.from_degrees(s, deg) for deg in (10.14, 60.0, 79.86, 90.0, 150.0) for s in (1.0, Frame.si().s)]


def arrays(frame, n=2000, seed=7):
    rng = np.random.default_rng(seed)
    return [GNArray(rng.uniform(-5, 5, n), rng.uniform(-5, 5, n) / frame.s, frame) for _ in range(2)]


def test_definitions_of_the_readings():
    # "Readings": Re z = a, Com z = b, Sh z = a + b s cos, Ht z = b s sin, |z|^2 = Sh^2 + Ht^2
    f = Frame.from_degrees(2.0, 60.0)
    z = GN(3.0, 5.0, f)
    assert (R.Re(z), R.Com(z)) == (3.0, 5.0)
    assert R.Sh(z) == pytest.approx(3.0 + 5.0 * 2.0 * 0.5, rel=1e-15)
    assert R.Ht(z) == pytest.approx(5.0 * 2.0 * math.sqrt(3) / 2, rel=1e-15)
    assert R.abs(z) ** 2 == pytest.approx(z.norm_sq(), rel=1e-15)


@pytest.mark.parametrize("f", FRAMES)
def test_identities_of_the_readings_on_arrays(f):
    z, w = arrays(f)
    close = lambda x, y, tol=1e-9: np.allclose(x, y, rtol=tol, atol=tol)  # noqa: E731
    # "Readings": |z|^2 = a^2 + 2ab s cos + b^2 s^2 = Sh^2 + Ht^2
    assert close(R.abs(z) ** 2, z.norm_sq()) and close(R.abs(z) ** 2, R.Sh(z) ** 2 + R.Ht(z) ** 2)
    # "Conjugate, skew flip, division": z + conj(z) = 2 Sh z ; Re conj(z) = 2 Sh z - Re z
    assert close(R.Re(z + z.conjugate()), 2 * R.Sh(z)) and close(R.Com(z + z.conjugate()) * f.s, 0.0)
    assert close(R.Re(z.conjugate()), 2 * R.Sh(z) - R.Re(z))
    # "Laws of the parts"
    zw = z * w
    assert close(R.Re(zw), R.Re(z) * R.Re(w) - f.s**2 * R.Com(z) * R.Com(w))
    assert close(R.Com(zw) * f.s, (R.Sh(z) * R.Com(w) + R.Sh(w) * R.Com(z)) * f.s)
    assert close(R.Sh(zw), R.Sh(z) * R.Sh(w) - R.Ht(z) * R.Ht(w))
    assert close(R.Ht(zw), R.Sh(z) * R.Ht(w) + R.Sh(w) * R.Ht(z))
    # "The norm is multiplicative": abs(zw) = abs(z) abs(w), an identity
    assert np.allclose(R.abs(zw), R.abs(z) * R.abs(w), rtol=1e-12, atol=0)
    # "Laws of the parts": |Re z| <= |z| / sin(phi_bar)
    assert np.all(np.abs(R.Re(z)) <= R.abs(z) / f.sin_phi() * (1 + 1e-12))


def test_readings_of_scalars_arrays_and_exact_numbers_agree():
    f = Frame.si()
    z = arrays(f, n=50)[0]
    for reading in (R.Re, R.Com, R.Sh, R.Ht, R.abs):
        assert np.allclose(reading(z), [reading(z.item(i)) for i in range(50)], rtol=1e-15, atol=0)
    with mpmath.workdps(50):
        e = Frame.from_degrees(mpmath.mpf(2), 60)
        x, y = GN(mpmath.mpf(3), mpmath.mpf(5), e), GN(mpmath.mpf("-1.5"), mpmath.mpf("0.25"), e)
        assert isinstance(R.abs(x), mpmath.mpf)
        assert mpmath.fabs(R.abs(x * y) - R.abs(x) * R.abs(y)) < mpmath.mpf(10) ** -47
        assert mpmath.fabs(R.abs(x) ** 2 - x.norm_sq()) < mpmath.mpf(10) ** -47


def test_every_preset_matches_the_table():
    # docs/05-scenarios-and-tests.md, section 0, "Matter presets" (kg, C)
    table = {
        "electron": (9.1093837e-31, -1.602176634e-19),
        "proton": (1.67262192e-27, 1.602176634e-19),
        "neutron": (1.67492750e-27, 0.0),
        "alpha": (6.6446573e-27, 3.204353268e-19),
        "dust grain +": (1e-15, 1e-16),
        "dust grain -": (1e-15, -1e-16),
        "moon": (7.342e22, 0.0),
        "Earth": (5.972e24, 0.0),
        "Sun": (1.989e30, 0.0),
        "Saturn": (5.683e26, 0.0),
    }
    assert {name: (b.m, b.q) for name, b in PRESETS.items()} == table
    assert all(preset(name).name == name for name in table)
    with pytest.raises(KeyError):
        preset("quark")


def test_mu_is_m_plus_q_G():
    f = Frame.si()
    proton = preset("proton")
    assert proton.mu(f) == GN(proton.m, proton.q, f) == proton.m + proton.q * GN.unit(f)
    earth = preset("Earth").with_charge(-5e5)
    assert (earth.m, earth.q, earth.name) == (5.972e24, -5e5, "Earth") and preset("Earth").q == 0.0
    assert CosmicMass(1.0, 2.0).mu(f).com == 2.0
