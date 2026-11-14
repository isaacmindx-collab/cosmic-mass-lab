"""Symbolic check of the derivation in team/notes/E2.2.md (question 11): the second field of a slowly
moving point cosmic mass.

Claim: a body of cosmic mass mu moving with constant velocity v has, to first order in v/c,

    E_cal(r, t) = -G mu (r - v t) / |r - v t|^3,        B_cal = (1/c^2) v x E_cal,

and these satisfy the compendium's field equations (F1-F4) away from the body:

    div B_cal = 0,
    curl B_cal = -(4 pi G / c^2) J_mu + (1/c^2) d/dt E_cal      (J_mu = 0 away from the body),
    curl E_cal = -d/dt B_cal                                    only up to terms of order (v/c)^2.

mu is a single symbol: the equations are linear and the same in both coordinates, so the check holds for
the Real part (m: g and B_g) and the Composer part (q: e and b) alike.

    python team/notes/E2.2_check.py      # prints each check; exit code 0 if all hold
"""

import sys

import sympy as sp

x, y, z, t = sp.symbols("x y z t", real=True)
G, mu, c = sp.symbols("G mu c", positive=True)
vx, vy, vz = sp.symbols("v_x v_y v_z", real=True)

r = sp.Matrix([x, y, z])
v = sp.Matrix([vx, vy, vz])
d = r - v * t
E = -G * mu * d / sp.sqrt(d.dot(d)) ** 3  # the field of the body at rest, carried along with it
B = v.cross(E) / c**2  # the claim


def div(f):
    return sp.diff(f[0], x) + sp.diff(f[1], y) + sp.diff(f[2], z)


def curl(f):
    return sp.Matrix(
        [
            sp.diff(f[2], y) - sp.diff(f[1], z),
            sp.diff(f[0], z) - sp.diff(f[2], x),
            sp.diff(f[1], x) - sp.diff(f[0], y),
        ]
    )


checks = {
    "div B_cal = 0": sp.simplify(div(B)) == 0,
    "curl B_cal = (1/c^2) dE_cal/dt (away from the body)": sp.simplify(curl(B) - sp.diff(E, t) / c**2)
    == sp.zeros(3, 1),
    "div E_cal = 0 (away from the body)": sp.simplify(div(E)) == 0,
}

# Faraday's law holds only to first order: curl E_cal is 0 (the field at rest), while -dB_cal/dt is of order
# v^2 / c^2 times E_cal / |r|. Show it vanishes as c -> infinity, faster than 1/c (it is exactly 1/c^2 times
# a term quadratic in v).
faraday = sp.simplify(curl(E) + sp.diff(B, t))
checks["curl E_cal + dB_cal/dt is of order (v/c)^2"] = all(
    sp.simplify(component * c**2).subs({vx: 0, vy: 0, vz: 0}) == 0
    and sp.Poly(sp.numer(sp.together(component * c**2)), vx, vy, vz).total_degree() >= 2
    for component in faraday
)

# The coordinates: with E_cal = g + e G and the source mu = m + q G, the Real part is B_g = (1/c^2) v x g and
# the Composer part b = (1/c^2) v x e; with E = -s^2 e and B = -s^2 b, B = (1/c^2) v x E: Biot-Savart for a
# slowly moving charge, with mu_0 = 4 pi K / c^2 (compendium). Check B = mu_0 q v x r_hat / (4 pi r^2) at t = 0.
K, q = sp.symbols("K q", positive=True)
s2 = K / G  # s^2 = K / G
e_field = -G * q * r / sp.sqrt(r.dot(r)) ** 3  # the Composer coordinate of E_cal for mu = q G (a pure charge)
b_field = v.cross(e_field) / c**2
B_field = -s2 * b_field
biot_savart = (4 * sp.pi * K / c**2) / (4 * sp.pi) * q * v.cross(r / sp.sqrt(r.dot(r))) / r.dot(r)
checks["B = -s^2 b is Biot-Savart (mu_0 = 4 pi K / c^2)"] = sp.simplify(B_field - biot_savart) == sp.zeros(3, 1)

for name, ok in checks.items():
    print(("holds  " if ok else "FAILS  ") + name)
sys.exit(0 if all(checks.values()) else 1)
