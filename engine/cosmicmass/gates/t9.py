"""The measured limits T9.1, T9.3 and T9.4 (decision D4), under the hypothesis L1a.

Setups and pass criteria: `docs/05-scenarios-and-tests.md`, section 2, T9; the numbers are
the book's (Chapter 9: a neutron would act as if it carried 9.0e-19 e; a charge in gravity
would act as if it sat in 1.14e11 V/m; a particle and its antiparticle near a neutral mass
would be pushed in opposite directions). The measured neutron charge, (-0.2 +/- 0.8)e-21 e,
is the value the book cites (Baumann et al., Phys. Rev. D 37, 1988). Pre-registrations:
`team/notes/T9.md`, `team/notes/T9.4.md`. The forces are evaluated once; nothing is integrated.
"""

import math

import numpy as np

from ..constants import SI
from ..fields import DirectSum
from ..laws import LawSpec, make_law
from ..matter import preset
from ..runner import run
from ..settings import load_settings
from .t0 import _pair, _relative_track

__all__ = ["t9_1", "t9_2", "t9_3", "t9_4", "NEUTRON_CHARGE_MEASURED", "STANDARD_GRAVITY",
           "HYDROGEN_BINDING_MEASURED", "BOHR_RADIUS"]

NEUTRON_CHARGE_MEASURED = (-0.2e-21, 0.8e-21)  # value and standard error, in units of e (as cited by the book)
STANDARD_GRAVITY = 9.80665  # m/s^2, the conventional standard acceleration of gravity
HYDROGEN_BINDING_MEASURED = 13.598  # eV, as cited by the book (Sansonetti 2005)
BOHR_RADIUS = 5.29177e-11  # m, as in T0.1b


def _forces(settings: dict):
    s = load_settings(settings)
    background = None if s.universe["background"] == "none" else s.universe["background"]
    fields = DirectSum(constants=SI, softening=0.0, background=background).at_bodies(s.state)
    return s, fields, s.make_law().forces(s.state, fields, s.frame)


def _settings(scenario, law, bodies, background="none", phi_bar_deg=79.86) -> dict:
    return {"scenario": scenario, "universe": {"phi_bar_deg": phi_bar_deg, "dimension": 2, "units": "SI",
                                               "background": background},
            "law": law, "bodies": bodies, "numerics": {"softening": 0.0, "steps": 0},
            "kind": "measurement-check", "preregistered": True}


def t9_1(strength: float = 1.0, phi_bar_deg: float = 79.86) -> dict:
    """T9.1: a neutron at 1e-10 m from a fixed proton, under L1a. Its response to the proton's
    electric field, as an effective charge `q_eff = -m_n / s`."""
    settings = _settings("T9.1", LawSpec(reading="L1a", strength=strength).to_dict(),
                         [{"preset": "proton", "x": [0.0, 0.0], "fixed": True},
                          {"preset": "neutron", "x": [1e-10, 0.0]}], phi_bar_deg=phi_bar_deg)
    s, fields, pair = _forces(settings)
    E = -s.frame.s**2 * fields.e[1]  # Maxwell's field of the proton at the neutron
    q_eff = float(np.dot(pair.composer[1], E) / np.dot(E, E))
    expected = -strength * preset("neutron").m / s.frame.s
    value, sigma = NEUTRON_CHARGE_MEASURED
    case = {
        "q_eff_coulomb": q_eff, "q_eff_in_e": q_eff / SI.e, "expected_in_e": expected / SI.e,
        "relative_error_vs_minus_m_over_s": abs(q_eff / expected - 1), "book_value_in_e": 9.0e-19,
        "composer_force": [float(c) for c in pair.composer[1]], "real_force": [float(c) for c in pair.real[1]],
        "measured_in_e": value, "measured_standard_error_in_e": sigma,
        "standard_errors_from_measurement": abs(q_eff / SI.e - value) / sigma,
        "largest_strength_allowed_at_two_standard_errors": strength * (abs(value) + 2 * sigma) / abs(q_eff / SI.e),
        "tolerance": {"rounds_to_book_value": 0.05e-19, "relative": 1e-12},
    }
    case["pass"] = bool(abs(abs(q_eff / SI.e) - strength * 9.0e-19) < strength * 0.05e-19
                        and case["relative_error_vs_minus_m_over_s"] < 1e-12)
    return {"id": "T9.1", "pass": case["pass"], "cases": {"neutron": case}, "runs": {"neutron": settings}}


def _share_factor(phi_bar_deg: float, strength: float, separations) -> tuple:
    """The pull on the electron of a proton-electron pair, Real plus Composer, over the Real pull,
    at each separation (forces once), under L1a with the charge share only."""
    law = LawSpec(reading="L1a", strength=strength, terms="-2 cos q E").to_dict()
    factors, pushes_back, runs = [], [], {}
    for a in separations:
        settings = _settings("T9.2", law, [{"preset": "proton", "x": [0.0, 0.0]},
                                           {"preset": "electron", "x": [a, 0.0]}], phi_bar_deg=phi_bar_deg)
        s, fields, pair = _forces(settings)
        towards = np.array([-1.0, 0.0])  # from the electron to the proton
        real = float(np.dot(pair.real[1], towards))
        factors.append((real + float(np.dot(pair.composer[1], towards))) / real)
        pushes_back.append(bool(float(np.dot(pair.composer[1], towards)) < 0))
        runs[f"forces_at_{a / BOHR_RADIUS:g}_a0"] = settings
    return factors, pushes_back, runs, s.frame


def t9_2(phi_bar_deg: float = 79.86, strength: float = 1.0, eta: float = 1e-3, orbit: bool = True,
         convergence: bool = True) -> dict:
    """T9.2: hydrogen under the charge share only (L5c), against the measured binding energy.
    (A) the pull is Coulomb's times `f = 1 - 2 lambda cos(phi_bar)` at every separation;
    (B) a circular orbit with the speed of that pull keeps its predicted period;
    (C) the book's scaling `f^2 x 13.598 eV` gives 5.71 eV."""
    separations = [k * BOHR_RADIUS for k in (0.5, 1.0, 2.0, 5.0)]
    factors, pushes_back, runs, frame = _share_factor(phi_bar_deg, strength, separations)
    expected = 1.0 - 2.0 * strength * frame.cos_phi()
    spread = max(abs(f / expected - 1) for f in factors)
    cases = {"pull": {
        "separations_in_a0": [a / BOHR_RADIUS for a in separations], "factor": factors, "expected": expected,
        "largest_relative_error": spread, "share_pushes_back": pushes_back,
        "tolerance": {"relative": 1e-12}}}
    cases["pull"]["pass"] = bool(spread < 1e-12 and all(pushes_back))

    f = float(np.mean(factors))
    binding = f * f * HYDROGEN_BINDING_MEASURED
    cases["binding"] = {
        "factor": f, "binding_energy_eV": binding, "book_value_eV": 5.71,
        "measured_eV": HYDROGEN_BINDING_MEASURED, "ratio_to_measured": binding / HYDROGEN_BINDING_MEASURED,
        "gap_eV": HYDROGEN_BINDING_MEASURED - binding,
        "method": "the book's scaling (binding energy grows with the square of the pull, Bohr 1913), with f "
                  "from the engine; not a quantum calculation by the engine",
        "tolerance": {"rounds_to_book_value_eV": 0.005}}
    cases["binding"]["pass"] = bool(abs(binding - 5.71) < 0.005)

    if orbit:
        p, e = preset("proton"), preset("electron")
        k = SI.G_N * p.m * e.m - expected * SI.K * p.q * e.q  # G_N m_p m_e + f K e^2: the weaker pull
        reduced = p.m * e.m / (p.m + e.m)
        period = 2 * math.pi * math.sqrt(reduced * BOHR_RADIUS**3 / k)
        speed = math.sqrt(k / (reduced * BOHR_RADIUS))
        law = LawSpec(reading="L1a", strength=strength, terms="-2 cos q E").to_dict()

        def measure(eta_value):
            settings = _pair("T9.2", p, e, BOHR_RADIUS, speed, phi_bar_deg,
                             {"t_end": period, "eta": eta_value, "record_every": 1}, kind="measurement-check")
            settings["law"] = law
            result = run(settings, out_root=None)
            t, r, angle = _relative_track(result)
            return result, 2 * math.pi * t[-1] / abs(angle[-1] - angle[0]), float(np.max(np.abs(r / BOHR_RADIUS - 1)))

        result, measured, radius_error = measure(eta)
        case = {"period": measured, "period_predicted": period, "period_error": abs(measured / period - 1),
                "speed": speed, "radius_largest_relative_change": radius_error,
                "energy_re_drift_reported_not_judged": result.summary["conservation"]["energy_re"],
                "steps": result.summary["steps"], "eta": eta,
                "tolerance": {"period": 1e-3, "radius": 1e-3, "convergence": 1e-2}}
        case["pass"] = bool(case["period_error"] < 1e-3 and radius_error < 1e-3)
        if convergence:
            half, quarter = measure(eta / 2)[1], measure(eta / 4)[1]
            case["convergence"] = {"period_eta": measured, "period_eta_half": half, "period_eta_quarter": quarter,
                                   "change_half_to_quarter": abs(half / quarter - 1)}
            case["pass"] = bool(case["pass"] and case["convergence"]["change_half_to_quarter"] < 1e-2)
        cases["orbit"] = case
        runs["orbit"] = result
    return {"id": "T9.2", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


def t9_3(phi_bar_deg: float = 79.86) -> dict:
    """T9.3: an electron in a uniform gravity `g`, under L1a with the term `s q g` only (L5a).
    The Composer force is that of an electric field `E_eq = s g`."""
    g = [0.0, -STANDARD_GRAVITY]
    settings = _settings("T9.3", LawSpec(reading="L1a", terms="s q g").to_dict(),
                         [{"preset": "electron", "x": [0.0, 0.0]}], background={"g": g}, phi_bar_deg=phi_bar_deg)
    s, fields, pair = _forces(settings)
    q = preset("electron").q
    E_eq = pair.composer[0] / q
    size, expected = float(np.linalg.norm(E_eq)), s.frame.s * STANDARD_GRAVITY
    case = {
        "equivalent_field_V_per_m": [float(c) for c in E_eq], "equivalent_field_size": size,
        "expected_s_times_g": expected, "relative_error_vs_s_g": abs(size / expected - 1),
        "book_value": 1.14e11, "g": STANDARD_GRAVITY,
        "composer_force": [float(c) for c in pair.composer[0]], "real_force": [float(c) for c in pair.real[0]],
        "composer_over_real": float(np.linalg.norm(pair.composer[0]) / np.linalg.norm(pair.real[0])),
        "tolerance": {"rounds_to_book_value": 0.005e11, "relative": 1e-12},
    }
    case["pass"] = bool(abs(size - 1.14e11) < 0.005e11 and case["relative_error_vs_s_g"] < 1e-12)
    return {"id": "T9.3", "pass": case["pass"], "cases": {"electron": case}, "runs": {"electron": settings}}


def t9_4(strength: float = 1.0, phi_bar_deg: float = 79.86) -> dict:
    """T9.4: a proton, then an antiproton (`m_p - e G`, the skew flip), at 7e6 m from the
    neutral Earth, under L1a with all terms. Their Composer forces are opposite."""
    proton, r = preset("proton"), 7e6
    bodies = {"proton": {"preset": "proton"},
              "antiproton": {"name": "antiproton", "m": proton.m, "q": -proton.q}}
    cases, runs, composer, real = {}, {}, {}, {}
    for name, body in bodies.items():
        pair_bodies = [{"preset": "Earth", "x": [0.0, 0.0], "fixed": True}, dict(body, x=[r, 0.0])]
        settings = _settings("T9.4", LawSpec(reading="L1a", strength=strength).to_dict(), pair_bodies,
                             phi_bar_deg=phi_bar_deg)
        s, fields, pair = _forces(settings)
        terms = {}
        for term in ("s q g", "-m E/s", "-2 cos q E"):
            spec = LawSpec(reading="L1a", strength=strength, terms=term).to_dict()
            terms[term] = [float(c) for c in _forces(dict(settings, law=spec))[2].composer[1]]
        g = fields.g[1]
        q = s.state.q[1]
        composer[name], real[name] = pair.composer[1], pair.real[1]
        expected = strength * s.frame.s * abs(q) * float(np.linalg.norm(g))
        size = float(np.linalg.norm(pair.composer[1]))
        towards_earth = bool(float(np.dot(pair.composer[1], g)) > 0)  # g points towards the Earth
        cases[name] = {
            "composer_force": [float(c) for c in pair.composer[1]], "real_force": [float(c) for c in pair.real[1]],
            "composer_terms": terms, "g": [float(c) for c in g], "composer_size": size,
            "expected_s_q_g": expected, "relative_error_vs_s_q_g": abs(size / expected - 1) if expected else size,
            "composer_towards_earth": towards_earth,
            "composer_over_real": size / float(np.linalg.norm(pair.real[1])),
        }
        runs[name] = settings
    p, a = cases["proton"], cases["antiproton"]
    scale = float(np.linalg.norm(composer["proton"]))
    total = float(np.linalg.norm(composer["proton"] + composer["antiproton"]))
    opposite = total / scale if scale else total
    checks = {
        "opposite_to_1e-15": opposite < 1e-15,
        "proton_pulled_antiproton_pushed": p["composer_towards_earth"] and not a["composer_towards_earth"],
        "size_s_e_g_to_1e-12": p["relative_error_vs_s_q_g"] < 1e-12 and a["relative_error_vs_s_q_g"] < 1e-12,
        "real_forces_equal": bool(np.array_equal(real["proton"], real["antiproton"])),
        "other_terms_zero": all(c == 0.0 for case in (p, a) for term in ("-m E/s", "-2 cos q E")
                                for c in case["composer_terms"][term]),
    }
    checks = {name: bool(ok) for name, ok in checks.items()}
    passed = all(checks.values())
    pair = {"relative_sum_of_composer_forces": opposite, "checks": checks, "pass": passed,
            "measurement": "none: the fall of a charged antiparticle has not been measured (book, Chapter 9)",
            "tolerance": {"opposite": 1e-15, "relative": 1e-12}}
    for case in (p, a):
        case["pass"] = passed
    return {"id": "T9.4", "pass": passed, "cases": {"proton": p, "antiproton": a, "pair": pair}, "runs": runs}
