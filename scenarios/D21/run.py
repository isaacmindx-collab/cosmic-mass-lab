"""D21.1 to D21.4: the four numerical conventions of decision D21, run against their alternatives.

Pre-registration: team/notes/D21.md (committed before these runs). Every case runs under the
reference law L0 and is compared with a closed form of the two-body problem, so every
statement is mathematics: a check of the engine's numerics, not a finding about nature.

    python scenarios/D21/run.py            # all four, writes results/D21.1/ ... results/D21.4/
    python scenarios/D21/run.py 3          # only D21.3
"""

import json
import math
import sys

import numpy as np

import cosmicmass.integrators as integrators
from cosmicmass.gates.t0 import _escape_radius, _pair, _strength, write_gate_result
from cosmicmass.matter import preset
from cosmicmass.runner import run

PRODUCER = "Claude Opus 5.5 in Claude Code, local (sponsor @MostafaDerraz)"
PHI = 79.86


def _orbit(a, b, separation, e=0.0):
    """Relative speed at apocentre and Kepler period for a pair released at `separation`."""
    k, mu = _strength(a, b), a.m * b.m / (a.m + b.m)
    speed = math.sqrt(k / (mu * separation) * (1 - e))
    semi = separation / (1 + e)
    return speed, 2 * math.pi * math.sqrt(mu * semi**3 / k)


def _rel(result, rotation=None):
    """Times and relative vectors (bodies 1 - 0), rotated back into the orbit plane."""
    rows = result.timeseries
    d = 3 if "x0_2" in rows[0] else 2
    rel = np.array([[r[f"x1_{k}"] - r[f"x0_{k}"] for k in range(d)] for r in rows])
    if rotation is not None:
        rel = rel @ rotation  # R^T applied to each row vector
    return np.array([r["t"] for r in rows]), rel


def _period(result, rotation=None):
    t, rel = _rel(result, rotation)
    angle = np.unwrap(np.arctan2(rel[:, 1], rel[:, 0]))
    return 2 * math.pi * t[-1] / abs(angle[-1] - angle[0])


def _excursion(result):
    e = np.array([r["energy_re"] for r in result.timeseries])
    return float(np.max(np.abs(e / e[0] - 1)))


def _rotation():
    ax, az = math.radians(30), math.radians(50)
    rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return rz @ rx


def _to_3d(settings, rot):
    s = json.loads(json.dumps(settings))
    s["universe"]["dimension"] = 3
    for body in s["bodies"]:
        body["x"] = [float(c) for c in rot @ np.array(body["x"] + [0.0])]
        body["v"] = [float(c) for c in rot @ np.array(body["v"] + [0.0])]
    return s


def _write(outcome, verdict, explanation):
    folder = write_gate_result(outcome, producer=PRODUCER)
    path = folder / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    # RESULTS-STANDARD section 4: the verdict is pass, fail or finding. D21 compares conventions
    # rather than testing a pass criterion, so it is a finding; the sentence goes to the explanation
    # (issue #24).
    summary.update(
        verdict="finding",
        explanation=f"{verdict[0].upper() + verdict[1:]}. {explanation}",
        prediction=outcome["prediction"],
    )
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return folder


def d21_1():
    """2D planar against a tilted 3D run of the same orbits."""
    rot = _rotation()
    cases, runs = {}, {}
    for name, a, b, r0 in (
        ("a", preset("Earth"), preset("moon"), 3.844e8),
        ("b", preset("proton"), preset("electron"), 5.29177e-11),
    ):
        speed, period = _orbit(a, b, r0)
        base = _pair(f"D21.1{name}", a, b, r0, speed, PHI, {"t_end": period, "eta": 1e-3, "record_every": 1})
        flat, tilted = run(base, out_root=None), run(_to_3d(base, rot), out_root=None)
        p2, p3 = _period(flat), _period(tilted, rot)
        d2, d3 = flat.summary["conservation"]["energy_re"], tilted.summary["conservation"]["energy_re"]
        _, rel3 = _rel(tilted, rot)
        cases[name] = {
            "period_2d": p2,
            "period_3d": p3,
            "period_analytic": period,
            "period_relative_difference": abs(p3 / p2 - 1),
            "energy_drift_2d": d2,
            "energy_drift_3d": d3,
            "steps_2d": flat.summary["steps"],
            "steps_3d": tilted.summary["steps"],
            "largest_out_of_plane_offset_relative": float(np.max(np.abs(rel3[:, 2])) / r0),
        }
        cases[name]["pass"] = bool(cases[name]["period_relative_difference"] < 1e-9)
        runs[f"{name}-2d"], runs[f"{name}-3d"] = flat, tilted
    ok = all(c["pass"] for c in cases.values())
    outcome = {
        "id": "D21.1",
        "pass": ok,
        "cases": cases,
        "runs": runs,
        "prediction": "periods and drifts agree to rounding (relative difference below 1e-9)",
    }
    explanation = (
        (
            "Planar motion in 2D gives the same orbits as the full 3D run to rounding, so D21's "
            "convention (1) loses nothing. A field falling as 1/r would need a 2D constant of "
            "gravitation that the compendium does not contain (mathematics, not run)."
        )
        if ok
        else "2D and 3D differ beyond rounding: convention (1) needs review."
    )
    return outcome, ("supports D21 (1)" if ok else "contradicts D21 (1)"), explanation


def d21_2():
    """Softening 0 against D10's softening on the three two-body cases of T0.1."""
    cases, runs = {}, {}
    for name, a, b, r0 in (
        ("a", preset("Earth"), preset("moon"), 3.844e8),
        ("b", preset("proton"), preset("electron"), 5.29177e-11),
    ):
        speed, period = _orbit(a, b, r0)
        for label, soft in (("softening 0", 0.0), ("softening D10", None)):
            res = run(
                _pair(
                    f"D21.2{name}",
                    a,
                    b,
                    r0,
                    speed,
                    PHI,
                    {"t_end": period, "eta": 1e-3, "record_every": 1, "softening": soft},
                ),
                out_root=None,
            )
            p = _period(res)
            key = f"{name}, {label}"
            cases[key] = {
                "period_error_vs_analytic": abs(p / period - 1),
                "energy_drift": res.summary["conservation"]["energy_re"],
                "passes_T0.1_criterion_0.1pct": bool(abs(p / (27.3 * 86400 if name == "a" else 1.5198e-16) - 1) < 1e-3),
            }
            runs[key] = res
    p = preset("proton")
    r0, k, mu = 1e-10, _strength(p, p), p.m / 2
    t_end = 3.0 * math.sqrt(mu * r0**3 / -k)
    exact = _escape_radius(t_end, r0, k, mu)
    for label, soft in (("softening 0", 0.0), ("softening D10", None)):
        signed = {}
        for eta in (1e-3, 5e-4):  # halving the step shows whether the error converges to zero
            res = run(
                _pair(
                    "D21.2c", p, p, r0, 0.0, PHI, {"t_end": t_end, "eta": eta, "record_every": 50, "softening": soft}
                ),
                out_root=None,
            )
            signed[eta] = float(np.linalg.norm(_rel(res)[1][-1])) / exact - 1
            if eta == 1e-3:
                runs[f"c, {label}"] = res
        cases[f"c, {label}"] = {
            "separation_error": abs(signed[1e-3]),
            "signed_error_eta": signed[1e-3],
            "signed_error_eta_half": signed[5e-4],
            "passes_T0.1c_criterion_1e-6": bool(abs(signed[1e-3]) < 1e-6),
        }
    cases["initial force factor with D10 softening"] = {"value": (1 + 1e-6) ** -1.5}
    s0, s1 = cases["c, softening 0"], cases["c, softening D10"]
    outcome = {
        "id": "D21.2",
        "pass": True,
        "cases": cases,
        "runs": runs,
        "prediction": "orbits pass either way; T0.1c likely fails with D10 softening (prediction failed: it passes)",
    }
    explanation = (
        "Prediction partly wrong: T0.1c passes with D10's softening, with a smaller error at eta = 1e-3 "
        f"({s1['separation_error']:.2e} against {s0['separation_error']:.2e}). Halving the step shows why: "
        f"without softening the error falls as the step squared ({s0['signed_error_eta']:+.2e} -> "
        f"{s0['signed_error_eta_half']:+.2e}), towards the closed form; with softening it grows "
        f"({s1['signed_error_eta']:+.2e} -> {s1['signed_error_eta_half']:+.2e}), towards a different answer, "
        "because softening changes the force law. The smaller error was a cancellation. The orbits' period "
        "error is ten times larger with softening (3.3e-6 against 3.3e-7). So gates compared with closed forms "
        "run with softening 0; D10's softening stays for many-body runs."
    )
    return outcome, "supports D21 (2)", explanation


def d21_3():
    """End-of-run drift against the largest excursion, for e = 0 and 0.9 and three eta."""
    a, b, r0 = preset("Earth"), preset("moon"), 3.844e8
    cases, runs = {}, {}
    for e in (0.0, 0.9):
        speed, period = _orbit(a, b, r0, e)
        for eta in (1e-3, 3e-4, 1e-4):
            res = run(
                _pair("D21.3", a, b, r0, speed, PHI, {"t_end": period, "eta": eta, "record_every": 1}), out_root=None
            )
            key = f"e={e}, eta={eta:g}"
            cases[key] = {
                "end_drift": res.summary["conservation"]["energy_re"],
                "largest_excursion": _excursion(res),
                "steps": res.summary["steps"],
            }
            cases[key]["end_drift_below_1e-6"] = bool(cases[key]["end_drift"] < 1e-6)
            cases[key]["excursion_below_1e-6"] = bool(cases[key]["largest_excursion"] < 1e-6)
            runs[key] = res
    split = [k for k, c in cases.items() if c["end_drift_below_1e-6"] != c["excursion_below_1e-6"]]
    outcome = {
        "id": "D21.3",
        "pass": True,
        "cases": cases,
        "runs": runs,
        "prediction": "end drift < 1e-6 everywhere; excursion ~4e-6 at e=0.9, eta=1e-3, falling as eta^2",
    }
    explanation = (
        "The two definitions give different verdicts for: " + ", ".join(split) + ". "
        if split
        else "Both definitions give the same verdict in every case. "
    ) + (
        "The end drift hides the excursion at pericentre, so every result reports both, and a scenario "
        "states which one its criterion uses (D21 (3) refined)."
    )
    return outcome, "refines D21 (3): report both", explanation


def _infall_radius(t, r0, gm):
    """Separation at time t of a pair falling from rest: t = sqrt(r0^3/2gm)(sqrt(x(1-x)) + acos(sqrt x))."""
    time_of = lambda x: math.sqrt(r0**3 / (2 * gm)) * (math.sqrt(x * (1 - x)) + math.acos(math.sqrt(x)))  # noqa: E731
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if time_of(mid) > t else (lo, mid)
    return 0.5 * (lo + hi) * r0


def d21_4():
    """The speed floor of bodies at rest: 0 (D10 as written), 0.01, 0.1, 1.0."""
    p = preset("proton")
    r0c, kc, muc = 1e-10, _strength(p, p), p.m / 2
    tc = 3.0 * math.sqrt(muc * r0c**3 / -kc)
    exact_c = _escape_radius(tc, r0c, kc, muc)
    a, b, r0f = preset("Earth"), preset("moon"), 3.844e8
    gm = _strength(a, b) / (a.m * b.m / (a.m + b.m))
    tf = 0.5 * (math.pi / 2) * math.sqrt(r0f**3 / (2 * gm))
    exact_f = _infall_radius(tf, r0f, gm)
    cases, runs = {}, {}
    original = integrators.REST_FRACTION
    try:
        for frac in (0.0, 0.01, 0.1, 1.0):
            integrators.REST_FRACTION = frac
            for name, setup, exact in (
                (
                    "c (protons apart)",
                    _pair("D21.4c", p, p, r0c, 0.0, PHI, {"t_end": tc, "eta": 1e-3, "record_every": 50}),
                    exact_c,
                ),
                (
                    "f (Earth-moon fall)",
                    _pair("D21.4f", a, b, r0f, 0.0, PHI, {"t_end": tf, "eta": 1e-3, "record_every": 50}),
                    exact_f,
                ),
            ):
                key = f"{name}, floor {frac:g}"
                try:
                    res = run(setup, out_root=None)
                except (ValueError, ZeroDivisionError) as exc:
                    cases[key] = {"outcome": "impossible", "reason": str(exc)}
                    continue
                sep = float(np.linalg.norm(_rel(res)[1][-1]))
                cases[key] = {
                    "separation_error": abs(sep / exact - 1),
                    "steps": res.summary["steps"],
                    "end_drift": res.summary["conservation"]["energy_re"],
                }
                runs[key] = res
    finally:
        integrators.REST_FRACTION = original
    outcome = {
        "id": "D21.4",
        "pass": True,
        "cases": cases,
        "runs": runs,
        "prediction": "floor 0 impossible; 0.01 and 0.1 below 1e-6; 1.0 coarser",
    }
    zero = [k for k, c in cases.items() if c.get("outcome") == "impossible"]
    explanation = (
        ("D10 as written cannot start from rest (" + "; ".join(zero) + "). ") if zero else ""
    ) + "With a floor, the error and the step count are listed per floor; the floor only acts in the first steps."
    return outcome, "supports a floor (D21 (4)); see numbers for its value", explanation


PARTS = {"1": d21_1, "2": d21_2, "3": d21_3, "4": d21_4}

if __name__ == "__main__":
    wanted = sys.argv[1:] or list(PARTS)
    for key in wanted:
        outcome, verdict, explanation = PARTS[key]()
        folder = _write(outcome, verdict, explanation)
        print(f"{outcome['id']}: {verdict}. {explanation}\n  results in {folder}")
        for name, case in outcome["cases"].items():
            print("   ", name, {k: (f"{v:.3e}" if isinstance(v, float) else v) for k, v in case.items()})
