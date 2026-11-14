"""The consistency gate T0 (tasks T0.1 to T0.5 and G1; decision D3).

Setups and pass criteria: `docs/05-scenarios-and-tests.md`, section 2, T0. Every case
runs under the reference law L0 and is compared with an analytic result of the
two-body problem or with a conservation law, so every statement here is a check of
the engine against mathematics. Choices fixed by decision D21: 2D is planar motion
with a `1/r^2` field; the two-body cases run with softening 0; "energy drift" is the
change of the energy at the end of the run.

Each function returns `{"id", "pass", "cases": {name: {..., "pass"}}, "runs": {...}}`.
The scenario scripts (`scenarios/T0.x/run.py`) call them in full and write the results;
the fast gate of CI (`engine/gates/`) calls them with shorter runs.
"""

import json
import math
from pathlib import Path

import numpy as np

from ..constants import SI
from ..fields import DirectSum
from ..frame import Frame
from ..integrators import StepContext
from ..laws import make_law
from ..matter import preset
from ..runner import run
from ..settings import load_settings
from ..stamp import build_stamp, engine_commit, make_run_id
from ..state import State

__all__ = ["t0_1", "t0_2", "t0_3", "t0_4", "t0_5", "run_gate", "write_gate_result", "ANGLES"]

ANGLES = (10.0, 45.0, 79.86, 90.0, 135.0, 170.0)  # T0.3
DAY = 86400.0


def _strength(a, b) -> float:
    """`G_N Re(mu_a mu_b) = G_N m_a m_b - K q_a q_b`: positive when the pair attracts."""
    return SI.G_N * a.m * b.m - SI.K * a.q * b.q


def _pair(scenario, a, b, separation, speed, phi_bar_deg, numerics, kind="mathematics") -> dict:
    """Settings of two bodies on the x axis, in their centre-of-mass frame, with relative speed
    `speed` along y."""
    total = a.m + b.m
    bodies = [
        {"name": a.name, "m": a.m, "q": a.q, "x": [-b.m / total * separation, 0.0], "v": [0.0, -b.m / total * speed]},
        {"name": b.name, "m": b.m, "q": b.q, "x": [a.m / total * separation, 0.0], "v": [0.0, a.m / total * speed]},
    ]
    return {
        "scenario": scenario,
        "universe": {"phi_bar_deg": phi_bar_deg, "dimension": 2, "units": "SI"},
        "law": {"id": "L0"},
        "bodies": bodies,
        "numerics": {"softening": 0.0, **numerics},
        "kind": kind,
        "preregistered": True,
    }


def _relative_track(result):
    """Times, separations and unwrapped angles of the pair, from the time series."""
    rows = result.timeseries
    t = np.array([r["t"] for r in rows])
    dx = np.array([r["x1_0"] - r["x0_0"] for r in rows])
    dy = np.array([r["x1_1"] - r["x0_1"] for r in rows])
    return t, np.hypot(dx, dy), np.unwrap(np.arctan2(dy, dx))


def _orbit_case(name, a, b, separation, reference_period, phi_bar_deg, periods, eta, convergence) -> tuple:
    strength = _strength(a, b)
    reduced = a.m * b.m / (a.m + b.m)
    analytic = 2 * math.pi * math.sqrt(reduced * separation**3 / strength)
    speed = math.sqrt(strength / (reduced * separation))

    def measure(eta_value):
        numerics = {"t_end": periods * analytic, "eta": eta_value, "record_every": 1}
        result = run(_pair(name, a, b, separation, speed, phi_bar_deg, numerics), out_root=None)
        t, r, angle = _relative_track(result)
        return result, 2 * math.pi * t[-1] / abs(angle[-1] - angle[0]), float(np.max(np.abs(r / separation - 1)))

    result, period, radius_error = measure(eta)
    drift = result.summary["conservation"]["energy_re"]
    case = {
        "period": period,
        "period_analytic": analytic,
        "period_reference": reference_period,
        "period_error_vs_reference": abs(period / reference_period - 1),
        "period_error_vs_analytic": abs(period / analytic - 1),
        "radius_largest_relative_change": radius_error,
        "energy_drift": drift,
        "steps": result.summary["steps"],
        "tolerance": {"period": 1e-3, "energy_drift": 1e-6},
    }
    case["pass"] = bool(case["period_error_vs_reference"] < 1e-3 and drift < 1e-6)
    if convergence:  # the same quantity at eta/2 and eta/4 (TEAM.md, section 5, step 5)
        half, quarter = measure(eta / 2)[1], measure(eta / 4)[1]
        case["convergence"] = {
            "period_eta": period,
            "period_eta_half": half,
            "period_eta_quarter": quarter,
            "change_half_to_quarter": abs(half / quarter - 1),
        }
    return case, result


def _escape_radius(t, r0, strength, reduced) -> float:
    """Separation at time `t` of two bodies released at rest at `r0` with a repulsive `k / r^2`
    force (`k = -strength > 0`): from `(1/2) mu r'^2 = k (1/r0 - 1/r)`,
    `t = sqrt(mu r0 / 2k) [sqrt(r (r - r0)) + r0 ln((sqrt(r) + sqrt(r - r0)) / sqrt(r0))]`."""
    k = -strength

    def time_of(r):
        return math.sqrt(reduced * r0 / (2 * k)) * (
            math.sqrt(r * (r - r0)) + r0 * math.log((math.sqrt(r) + math.sqrt(r - r0)) / math.sqrt(r0))
        )

    low, high = r0, 2 * r0
    while time_of(high) < t:
        high *= 2
    for _ in range(200):
        mid = 0.5 * (low + high)
        low, high = (mid, high) if time_of(mid) < t else (low, mid)
    return 0.5 * (low + high)


def _escape_case(phi_bar_deg, eta, convergence) -> tuple:
    p, r0 = preset("proton"), 1e-10
    strength, reduced = _strength(p, p), p.m / 2
    t_end = 3.0 * math.sqrt(reduced * r0**3 / -strength)  # three times the natural time of the pair

    def measure(eta_value):
        numerics = {"t_end": t_end, "eta": eta_value, "record_every": 50}
        result = run(_pair("T0.1c", p, p, r0, 0.0, phi_bar_deg, numerics), out_root=None)
        return result, float(_relative_track(result)[1][-1])

    result, separation = measure(eta)
    analytic = _escape_radius(t_end, r0, strength, reduced)
    case = {
        "t_end": t_end,
        "separation": separation,
        "separation_analytic": analytic,
        "separation_error": abs(separation / analytic - 1),
        "energy_drift": result.summary["conservation"]["energy_re"],
        "steps": result.summary["steps"],
        "eta": eta,
        "tolerance": {"separation": 1e-6},
    }
    case["pass"] = bool(case["separation_error"] < 1e-6)
    if convergence:
        half, quarter = measure(eta / 2)[1], measure(eta / 4)[1]
        case["convergence"] = {
            "separation_eta": separation,
            "separation_eta_half": half,
            "separation_eta_quarter": quarter,
            "change_half_to_quarter": abs(half / quarter - 1),
        }
    return case, result


def t0_1(
    phi_bar_deg: float = 79.86,
    periods: float = 1.0,
    eta: float = 1e-3,
    escape_eta: float = 1e-3,
    convergence: bool = False,
) -> dict:
    """T0.1: (a) Earth and moon, (b) electron and proton at the Bohr radius, (c) two protons at rest."""
    cases, runs = {}, {}
    cases["a"], runs["a"] = _orbit_case(
        "T0.1a", preset("Earth"), preset("moon"), 3.844e8, 27.3 * DAY, phi_bar_deg, periods, eta, convergence
    )
    cases["b"], runs["b"] = _orbit_case(
        "T0.1b", preset("proton"), preset("electron"), 5.29177e-11, 1.5198e-16, phi_bar_deg, periods, eta, convergence
    )
    cases["c"], runs["c"] = _escape_case(phi_bar_deg, escape_eta, convergence)
    return {"id": "T0.1", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


def cloud_settings(n: int = 200, steps: int = 10_000, seed: int = 12345, eta: float = 1e-3, side: float = 2e-7) -> dict:
    """T0.2: `n` random electrons, protons and neutrons in a square box with reflecting walls."""
    rng = np.random.default_rng(seed)
    kinds = rng.choice(["electron", "proton", "neutron"], size=n)
    spread = {"electron": 1e6, "proton": 2e4, "neutron": 2e4}  # velocity spread of each kind, m/s
    half = side / 2
    bodies = [
        {
            "preset": str(kind),
            "x": [float(c) for c in rng.uniform(-0.98 * half, 0.98 * half, 2)],
            "v": [float(c) for c in rng.normal(0.0, spread[str(kind)], 2)],
        }
        for kind in kinds
    ]
    return {
        "scenario": "T0.2",
        "universe": {
            "dimension": 2,
            "units": "SI",
            "boundary": "reflecting",
            "box": {"lower": [-half, -half], "upper": [half, half]},
        },
        "law": {"id": "L0"},
        "bodies": bodies,
        "numerics": {"steps": steps, "eta": eta, "seed": seed, "record_every": max(1, steps // 500)},
        "kind": "mathematics",
        "preregistered": True,
    }


def t0_2(n: int = 200, steps: int = 10_000, seed: int = 12345, eta: float = 1e-3, convergence: bool = False) -> dict:
    """T0.2: mass and charge exactly constant; energy and momentum drift below 1e-6. The walls take
    momentum, so the momentum checked is that of the bodies plus what they gave to the walls."""

    def measure(n_value, eta_value):
        result = run(cloud_settings(n_value, steps, seed, eta_value), out_root=None)
        c = result.summary["conservation"]
        return result, {
            "mass_drift": c["mass"],
            "charge_drift": c["charge"],
            "energy_drift": c["energy_re"],
            "momentum_drift_with_walls": result.summary["momentum_with_walls_drift"],
            "momentum_drift_bodies_only": c["momentum"],
            "wall_hits": result.summary["wall_hits"],
            "t_end": result.summary["t_end"],
            "steps": result.summary["steps"],
        }

    result, case = measure(n, eta)
    case["tolerance"] = {"mass": 0.0, "charge": 0.0, "energy_drift": 1e-6, "momentum_drift": 1e-6}
    case["pass"] = bool(
        case["mass_drift"] == 0.0
        and case["charge_drift"] in (0.0, None)
        and case["energy_drift"] < 1e-6
        and case["momentum_drift_with_walls"] < 1e-6
    )
    if convergence:  # the drifts at eta/2 and eta/4, and with half and twice the bodies
        case["convergence"] = {
            label: {k: m[k] for k in ("energy_drift", "momentum_drift_with_walls")}
            for label, m in (
                ("eta_half", measure(n, eta / 2)[1]),
                ("eta_quarter", measure(n, eta / 4)[1]),
                ("n_half", measure(n // 2, eta)[1]),
                ("n_double", measure(2 * n, eta)[1]),
            )
        }
    return {"id": "T0.2", "pass": case["pass"], "cases": {"cloud": case}, "runs": {"cloud": result}}


def t0_3(periods: float = 1.0, eta: float = 1e-3, angles=ANGLES) -> dict:
    """T0.3: T0.1 at six frame angles; every `Re` result identical to machine precision. Here the
    final positions and velocities and the measured quantities are compared bit for bit."""
    reference, cases, runs = None, {}, {}
    for angle in angles:
        outcome = t0_1(angle, periods, eta)
        finals = {
            k: (r.state.x.tobytes(), r.state.v.tobytes(), r.summary["steps"], r.summary["final"]["energy_re"])
            for k, r in outcome["runs"].items()
        }
        reference = finals if reference is None else reference
        cases[f"{angle:g} deg"] = {
            "identical_to_first_angle": finals == reference,
            "periods": {k: outcome["cases"][k].get("period") for k in ("a", "b")},
            "separation_c": outcome["cases"]["c"]["separation"],
            "pass": bool(finals == reference and outcome["pass"]),
        }
        runs[f"{angle:g} deg"] = outcome["runs"]["a"]
    return {"id": "T0.3", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


def t0_4(phi_bar_deg: float = 79.86) -> dict:
    """T0.4: universal free fall. A neutral Earth, fixed; an electron, a proton, a neutron and a
    dust grain, each alone at 7e6 m, at rest: all fall with `G_N M / r^2` within 1e-12."""
    earth, r = preset("Earth"), 7e6
    expected = SI.G_N * earth.m / r**2
    frame, cases, runs = Frame.si(phi_bar_deg), {}, {}
    for name in ("electron", "proton", "neutron", "dust grain +"):
        body = preset(name)
        state = State.from_bodies([earth, body], [[0.0, 0.0], [r, 0.0]], fixed=[True, False])
        ctx = StepContext(make_law("L0"), DirectSum(constants=SI), frame)
        a = ctx.acceleration(state)[1]
        cases[name] = {
            "acceleration": [float(c) for c in a],
            "expected": expected,
            "relative_error": abs(-a[0] / expected - 1),
            "tolerance": 1e-12,
        }
        cases[name]["pass"] = bool(cases[name]["relative_error"] < 1e-12 and a[1] == 0.0)
        runs[name] = {
            "scenario": "T0.4",
            "universe": {"phi_bar_deg": phi_bar_deg, "dimension": 2, "units": "SI"},
            "law": {"id": "L0"},
            "numerics": {"softening": 0.0, "steps": 0},
            "bodies": [{"preset": "Earth", "x": [0.0, 0.0], "fixed": True}, {"preset": name, "x": [r, 0.0]}],
            "kind": "mathematics",
            "preregistered": True,
        }
    spread = max(c["acceleration"][0] for c in cases.values()) - min(c["acceleration"][0] for c in cases.values())
    cases["all bodies"] = {
        "largest_relative_difference": abs(spread) / expected,
        "tolerance": 1e-12,
        "pass": bool(abs(spread) / expected < 1e-12),
    }
    return {"id": "T0.4", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


def t0_5(points_per_side: int = 21) -> dict:
    """T0.5: the static field of one proton on a grid. The Composer part gives
    `E = -s^2 e = K e / r^2` within 1e-6; the Real part gives `g = -G_N m_p / r^2`."""
    proton, s = preset("proton"), Frame.si().s
    state = State.from_bodies([proton], [[0.0, 0.0]])
    axis = np.linspace(-1e-9, 1e-9, points_per_side)
    grid = np.array([[x, y] for x in axis for y in axis if (x, y) != (0.0, 0.0)])
    field = DirectSum(constants=SI).sample(state, grid)
    r = np.linalg.norm(grid, axis=1, keepdims=True)
    coulomb = SI.K * proton.q * grid / r**3
    newton = -SI.G_N * proton.m * grid / r**3
    error_e = float(np.max(np.linalg.norm(-s * s * field.e - coulomb, axis=1) / np.linalg.norm(coulomb, axis=1)))
    error_g = float(np.max(np.linalg.norm(field.g - newton, axis=1) / np.linalg.norm(newton, axis=1)))
    case = {
        "grid_points": len(grid),
        "largest_relative_error_E": error_e,
        "largest_relative_error_g": error_g,
        "tolerance": 1e-6,
        "pass": bool(error_e < 1e-6 and error_g < 1e-6),
    }
    settings = {
        "scenario": "T0.5",
        "universe": {"dimension": 2, "units": "SI"},
        "law": {"id": "L0"},
        "bodies": [{"preset": "proton", "x": [0.0, 0.0]}],
        "numerics": {"softening": 0.0, "steps": 0},
        "kind": "mathematics",
        "preregistered": True,
    }
    return {"id": "T0.5", "pass": case["pass"], "cases": {"proton": case}, "runs": {"proton": settings}}


def run_gate(fast: bool = True) -> dict:
    """All of T0. `fast` is the gate of CI: shorter orbits and a smaller cloud, same criteria."""
    if fast:
        parts = [t0_1(periods=1.0), t0_2(n=40, steps=400), t0_3(periods=0.05), t0_4(), t0_5(points_per_side=9)]
    else:
        parts = [t0_1(convergence=True), t0_2(convergence=True), t0_3(), t0_4(), t0_5()]
    return {"pass": all(p["pass"] for p in parts), "parts": {p["id"]: p for p in parts}}


def write_gate_result(
    outcome: dict,
    out_root="results",
    producer: str = "",
    now=None,
    kind: str = "mathematics",
    law: str = "the reference law L0",
) -> Path:
    """Write one gate test to `results/<ID>/<run-id>/`: `summary.json` (cases and verdict),
    `stamp.json` (the stamp of every case) and, for the cases that ran, `timeseries-<case>.csv`."""
    import csv

    commit = engine_commit()
    run_id = make_run_id(commit, now)
    folder = Path(out_root) / outcome["id"] / run_id
    folder.mkdir(parents=True, exist_ok=False)
    stamps = {}
    for name, item in outcome["runs"].items():
        if isinstance(item, dict):  # a case computed without the runner: stamp its settings
            stamps[name] = build_stamp(load_settings(item), 0.0, run_id, commit)
        else:
            stamps[name] = dict(item.stamp, run_id=run_id)
            # only letters, digits, ".", "-", "=", "," and "_": some systems refuse ":" or "/" in a file name
            safe = "".join(c if c.isalnum() or c in ".-=," else "_" for c in name)
            with open(folder / f"timeseries-{safe}.csv", "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(item.timeseries[0]))
                writer.writeheader()
                # at most about 500 rows are kept on disk (the analysis used every row)
                keep = max(1, -(-len(item.timeseries) // 500))
                rows = item.timeseries[::keep]
                writer.writerows(rows if rows[-1] is item.timeseries[-1] else rows + [item.timeseries[-1]])
    for stamp in stamps.values():
        stamp["producer"] = producer
    stamp = {
        "scenario": outcome["id"],
        "run_id": run_id,
        "engine_commit": commit,
        "kind": kind,
        "preregistered": True,
        "producer": producer,
        "cases": stamps,
    }
    verdict = "pass" if outcome["pass"] else "fail"
    summary = {
        "scenario": outcome["id"],
        "verdict": verdict,
        "cases": outcome["cases"],
        "explanation": f"{outcome['id']} under {law}: "
        + ("every case meets its criterion." if outcome["pass"] else "at least one case fails."),
    }
    for name, data in (("stamp.json", stamp), ("summary.json", summary)):
        (folder / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return folder
