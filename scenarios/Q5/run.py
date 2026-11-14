"""Q5: the nearest-neighbour step (rule B of Q4) on a fast passage, and a pair guard (rule C).

Pre-registration: team/notes/Q5.md. Law L0 only; every statement is mathematics (a check of
the numerical method). Rule C is written here, not in the engine: no default changes.

    python scenarios/Q5/run.py        # writes results/Q5/<run-id>/
"""

import math
import sys

import numpy as np

from cosmicmass.constants import SI, scaled
from cosmicmass.energy import energy_l0
from cosmicmass.fields import DirectSum
from cosmicmass.gates.t0 import _pair, _strength, write_gate_result
from cosmicmass.integrators import StepContext, VelocityVerlet
from cosmicmass.matter import preset
from cosmicmass.settings import load_settings

PRODUCER = "Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz)"
PHI = 79.86
ETA = 1e-3
DAY = 86400.0


def pair_guard(state, eta: float) -> float:
    """`eta min_(i<j) r_ij / |v_i - v_j|` over the alive bodies (infinite if no pair moves apart or together)."""
    x, v = state.x[state.alive], state.v[state.alive]
    i, j = np.triu_indices(len(x), 1)
    r = np.linalg.norm(x[i] - x[j], axis=1)
    w = np.linalg.norm(v[i] - v[j], axis=1)
    moving = w > 0
    return float(eta * np.min(r[moving] / w[moving])) if np.any(moving) else math.inf


def simulate(settings: dict, rule: str, eta: float, track=None) -> dict:
    """Integrate `settings` with the engine's velocity Verlet, the step of `rule` ("A", "B" or "C").
    `track(state)` is called after every step (for example to record an angle)."""
    s = load_settings(settings)
    constants = SI if s.universe["units"] == "SI" else scaled()
    state = s.state.copy()
    ctx = StepContext(s.make_law(), DirectSum(constants=constants, softening=0.0), s.frame, eta=eta,
                      speed_reference="absolute" if rule == "A" else "neighbour")
    integrator, t_end, steps = VelocityVerlet(), s.numerics["t_end"], 0
    e0 = energy_l0(state, s.frame, constants)["total"]
    excursion = 0.0
    while state.t < t_end:
        dt = integrator.next_dt(state, ctx)
        if rule == "C":
            dt = min(dt, pair_guard(state, eta))
        last = state.t + dt >= t_end
        state = integrator.step(state, min(dt, t_end - state.t), ctx)
        if last:
            state.t = float(t_end)
        steps += 1
        excursion = max(excursion, abs(energy_l0(state, s.frame, constants)["total"] / e0 - 1))
        if track is not None:
            track(state)
    drift = abs(energy_l0(state, s.frame, constants)["total"] / e0 - 1)
    return {"state": state, "steps": steps, "energy_end_drift": drift, "energy_largest_excursion": excursion}


def trap_settings() -> dict:
    """Setup 1: a light, loose pair passes fast by a heavy body whose nearest neighbour is its companion."""
    bodies = [{"name": "H", "m": 1.0, "q": 0.0, "x": [0.0, 0.0]},
              {"name": "companion", "m": 1e-3, "q": 0.0, "x": [1.0, 0.0], "v": [0.0, 1.0]},
              {"name": "pair a", "m": 1e-12, "q": 0.0, "x": [-60.0, 1.5], "v": [300.0, 0.0]},
              {"name": "pair b", "m": 1e-12, "q": 0.0, "x": [-60.0, 1.51], "v": [300.0, 0.0]}]
    return {"scenario": "Q5", "universe": {"units": "scaled", "dimension": 2}, "law": {"id": "L0"}, "bodies": bodies,
            "numerics": {"softening": 0.0, "t_end": 0.4}, "kind": "mathematics", "preregistered": True}


def trap(rule: str, eta: float) -> dict:
    out = simulate(trap_settings(), rule, eta)
    state = out.pop("state")
    out["deflection"] = float(np.mean(state.v[2:4, 1]))  # Delta v_y of the pair's centre of mass (equal masses)
    out["pair_separation"] = float(np.linalg.norm(state.x[3] - state.x[2]))
    return out


def earth_moon(rule: str, boost: float) -> dict:
    earth, moon = preset("Earth"), preset("moon")
    k, mu, r = _strength(earth, moon), earth.m * moon.m / (earth.m + moon.m), 3.844e8
    period, speed = 2 * math.pi * math.sqrt(mu * r**3 / k), math.sqrt(k / (mu * r))
    settings = _pair("Q5", earth, moon, r, speed, PHI, {"t_end": period})
    for body in settings["bodies"]:
        body["v"][0] += boost
    angles = []
    out = simulate(settings, rule, ETA, track=lambda s: angles.append(math.atan2(*(s.x[1] - s.x[0])[::-1])))
    swept = float(np.abs(np.unwrap(np.array(angles))[-1] - math.atan2(0.0, r)))
    out.pop("state")
    out["period_error"] = abs(2 * math.pi * period / swept / period - 1)
    return out


def sun_earth_moon(rule: str, eta: float) -> dict:
    bodies = [{"preset": "Sun", "x": [0.0, 0.0]},
              {"preset": "Earth", "x": [1.496e11, 0.0], "v": [0.0, 29780.0]},
              {"preset": "moon", "x": [1.496e11 + 3.844e8, 0.0], "v": [0.0, 29780.0 + 1022.0]}]
    settings = {"scenario": "Q5", "universe": {"phi_bar_deg": PHI, "dimension": 2, "units": "SI"}, "law": {"id": "L0"},
                "bodies": bodies, "numerics": {"softening": 0.0, "t_end": 27.3 * DAY}, "kind": "mathematics",
                "preregistered": True}
    out = simulate(settings, rule, eta)
    state = out.pop("state")
    out["earth_moon_separation"] = float(np.linalg.norm(state.x[2] - state.x[1]))
    return out


def q5() -> dict:
    cases = {}
    # 1: the trap; reference C at eta/8, with eta/2 and eta/4 for convergence
    for name, rule, eta in (("1: trap; B", "B", ETA), ("1: trap; C", "C", ETA), ("1: trap; C, eta/2", "C", ETA / 2),
                            ("1: trap; C, eta/4", "C", ETA / 4), ("1: trap; C, eta/8 (reference)", "C", ETA / 8)):
        cases[name] = trap(rule, eta)
    ref = cases["1: trap; C, eta/8 (reference)"]
    for case in cases.values():
        case["deflection_error_vs_reference"] = abs(case["deflection"] / ref["deflection"] - 1)
        case["pair_separation_error_vs_reference"] = abs(case["pair_separation"] / ref["pair_separation"] - 1)
    b, L = 1.5, 60.0
    impulse = 2.0 / (b * 300.0) * L / math.sqrt(L * L + b * b)
    cases["1: trap; A (not run)"] = {"steps_from_the_rule": int(round(0.4 / (ETA * 0.01 / 300.0))),
                                     "why_not_run": "dt <= eta l / |v| = 3.3e-8 for each pair member"}
    # 2: Earth and moon, own frame and boosted
    for frame, boost in (("own frame", 0.0), ("plus 29780 m per s", 29780.0)):
        for rule in ("B", "C"):
            cases[f"2: Earth-moon, {frame}; {rule}"] = earth_moon(rule, boost)
    # 3: Sun, Earth and moon; reference B with eta = 1.25e-4, as in Q4
    for name, rule, eta in (("3: Sun-Earth-moon; B", "B", ETA), ("3: Sun-Earth-moon; C", "C", ETA),
                            ("3: Sun-Earth-moon; B, eta = 1.25e-4 (reference)", "B", 1.25e-4)):
        cases[name] = sun_earth_moon(rule, eta)
    ref3 = cases["3: Sun-Earth-moon; B, eta = 1.25e-4 (reference)"]["earth_moon_separation"]
    for name in ("3: Sun-Earth-moon; B", "3: Sun-Earth-moon; C"):
        cases[name]["separation_error_vs_reference"] = abs(cases[name]["earth_moon_separation"] / ref3 - 1)

    get = cases.__getitem__
    tb, tc = get("1: trap; B"), get("1: trap; C")
    em = {k: get(f"2: Earth-moon, {k}") for k in ("own frame; B", "own frame; C", "plus 29780 m per s; C")}
    sb, sc = get("3: Sun-Earth-moon; B"), get("3: Sun-Earth-moon; C")
    predictions = {
        "1: B's deflection error between 1e-4 and 1e-2": bool(1e-4 <= tb["deflection_error_vs_reference"] <= 1e-2),
        "1: B takes a few hundred to about 2,000 steps": bool(200 <= tb["steps"] <= 2_000),
        "1: C's deflection within 1e-5 of the reference": bool(tc["deflection_error_vs_reference"] < 1e-5),
        "1: C takes 4,000 to 20,000 steps": bool(4_000 <= tc["steps"] <= 20_000),
        "1: the reference agrees with the impulse within 1%": bool(abs(ref["deflection"] / impulse - 1) < 0.01),
        "1: the reference has converged (eta/4 to eta/8 below 1e-6)": bool(
            get("1: trap; C, eta/4")["deflection_error_vs_reference"] < 1e-6),
        "2: C's steps within 10% of B's, own frame": bool(abs(em["own frame; C"]["steps"] / em["own frame; B"]["steps"] - 1) < 0.1),
        "2: C takes the same steps in both frames": bool(em["own frame; C"]["steps"] == em["plus 29780 m per s; C"]["steps"]),
        "2: C's period error within a factor 2 of B's": bool(
            em["own frame; C"]["period_error"] <= 2 * em["own frame; B"]["period_error"]),
        "3: C's steps within 10% of B's": bool(abs(sc["steps"] / sb["steps"] - 1) < 0.1),
        "3: C within 1e-5 of the reference": bool(sc["separation_error_vs_reference"] < 1e-5),
    }
    cases["predictions"] = {"flags": predictions, "impulse_estimate": impulse, "pass": all(predictions.values())}
    for case in cases.values():
        case.setdefault("pass", True)  # measurements carry no criterion; the predictions do
    runs = {"trap": trap_settings()}
    return {"id": "Q5", "pass": cases["predictions"]["pass"], "cases": cases, "runs": runs}


if __name__ == "__main__":
    outcome = q5()
    folder = write_gate_result(outcome, producer=sys.argv[1] if len(sys.argv) > 1 else PRODUCER,
                               kind="mathematics", law="the reference law L0 (a test of the step rule)")
    for flag, ok in outcome["cases"]["predictions"]["flags"].items():
        print(f"{'holds' if ok else 'FAILS'}  {flag}")
    for name, case in outcome["cases"].items():
        if "steps" in case:
            extra = {k: f"{v:.3g}" for k, v in case.items() if k.endswith("error_vs_reference") or k == "period_error"}
            print(f"{name}: {case['steps']} steps {extra}")
    print(f"results in {folder}")
