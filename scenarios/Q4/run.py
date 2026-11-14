"""Q4: does the adaptive step depend on the frame in which the bodies are described?

Pre-registration: team/notes/Q4.md (committed before any code or run). Reference law L0.
Candidate A is the current step rule (decisions D10 and D21): each body's own speed and
acceleration. Candidate B measures them relative to the body's nearest neighbour. B is an
option of the integrator (`numerics.speed_reference = "neighbour"`), NOT a default.

    python scenarios/Q4/run.py        # writes results/Q4/<run-id>/
"""

import math

import numpy as np

from cosmicmass.constants import SI
from cosmicmass.gates.t0 import _escape_radius, _pair, _relative_track, _strength, write_gate_result
from cosmicmass.matter import preset
from cosmicmass.runner import run

PRODUCER = "Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz)"
PHI = 79.86
RULES = {"A (absolute)": "absolute", "B (nearest neighbour)": "neighbour"}


def boosted(settings: dict, boost) -> dict:
    """The same settings with a uniform velocity added to every body."""
    out = {**settings, "bodies": [{**b, "v": [v + w for v, w in zip(b["v"], boost)]} for b in settings["bodies"]]}
    return out


def _energy(result) -> dict:
    values = np.array([row["energy_re"] for row in result.timeseries])
    change = np.abs(values / values[0] - 1)
    return {"end_drift": float(change[-1]), "largest_excursion": float(change.max())}


def q4() -> dict:
    cases, runs = {}, {}
    earth, moon, proton, sun = preset("Earth"), preset("moon"), preset("proton"), preset("Sun")

    # 1 and 2: Earth and moon, at rest as a whole and with the Earth's orbital speed
    k, mu, r = _strength(earth, moon), earth.m * moon.m / (earth.m + moon.m), 3.844e8
    period, speed = 2 * math.pi * math.sqrt(mu * r**3 / k), math.sqrt(k / (mu * r))
    tracks = {}
    for frame_name, boost in (("1: Earth-moon, own frame", [0.0, 0.0]), ("2: Earth-moon, plus 29780 m per s", [29780.0, 0.0])):
        for rule, reference in RULES.items():
            numerics = {"t_end": period, "record_every": 1, "speed_reference": reference}
            result = run(boosted(_pair("Q4", earth, moon, r, speed, PHI, numerics), boost), out_root=None)
            t, sep, angle = _relative_track(result)
            measured = 2 * math.pi * t[-1] / abs(angle[-1] - angle[0])
            name = f"{frame_name}; {rule}"
            cases[name] = {"steps": result.summary["steps"], "period_error": abs(measured / period - 1), **_energy(result)}
            runs[name], tracks[name] = result, (t, sep)
    # B must give the same motion in both frames: compare the separations at the end
    own, moved = tracks["1: Earth-moon, own frame; B (nearest neighbour)"], tracks["2: Earth-moon, plus 29780 m per s; B (nearest neighbour)"]
    cases["2: Earth-moon, plus 29780 m per s; B (nearest neighbour)"]["final_separation_vs_own_frame"] = float(abs(moved[1][-1] / own[1][-1] - 1))

    # 3: two protons, at rest as a whole and with 1e6 m/s
    r0, k_pp, mu_pp = 1e-10, _strength(proton, proton), proton.m / 2
    t_end = 3.0 * math.sqrt(mu_pp * r0**3 / -k_pp)
    exact = _escape_radius(t_end, r0, k_pp, mu_pp)
    for frame_name, boost in (("3: two protons, own frame", [0.0, 0.0]), ("3: two protons, plus 1e6 m per s", [1e6, 0.0])):
        for rule, reference in RULES.items():
            numerics = {"t_end": t_end, "record_every": 50, "speed_reference": reference}
            result = run(boosted(_pair("Q4", proton, proton, r0, 0.0, PHI, numerics), boost), out_root=None)
            name = f"{frame_name}; {rule}"
            cases[name] = {"steps": result.summary["steps"],
                           "separation_error": float(abs(_relative_track(result)[1][-1] / exact - 1)), **_energy(result)}
            runs[name] = result

    # 4: Sun, Earth and moon for 27.3 days; reference: rule B with eta = 1.25e-4
    v_earth = math.sqrt(SI.G_N * sun.m / 1.496e11)
    bodies = [{"preset": "Sun", "x": [0.0, 0.0], "v": [0.0, 0.0]},
              {"preset": "Earth", "x": [1.496e11, 0.0], "v": [0.0, 29780.0]},
              {"preset": "moon", "x": [1.496e11 + 3.844e8, 0.0], "v": [0.0, 29780.0 + 1022.0]}]

    def three(reference, eta):
        settings = {"scenario": "Q4", "universe": {"phi_bar_deg": PHI, "dimension": 2, "units": "SI"}, "law": {"id": "L0"},
                    "bodies": bodies, "kind": "mathematics", "preregistered": True,
                    "numerics": {"softening": 0.0, "t_end": 27.3 * 86400.0, "eta": eta, "speed_reference": reference,
                                 "record_every": 200}}
        result = run(settings, out_root=None)
        return result, float(np.linalg.norm(result.state.x[2] - result.state.x[1]))

    reference_run, reference_separation = three("neighbour", 1.25e-4)
    for rule, reference in RULES.items():
        result, separation = three(reference, 1e-3)
        name = f"4: Sun-Earth-moon; {rule}"
        cases[name] = {"steps": result.summary["steps"], "earth_moon_separation": separation,
                       "separation_vs_reference": abs(separation / reference_separation - 1), **_energy(result)}
        runs[name] = result
    cases["4: Sun-Earth-moon; reference (B, eta = 1.25e-4)"] = {
        "steps": reference_run.summary["steps"], "earth_moon_separation": reference_separation, **_energy(reference_run),
        "circular_speed_of_the_earth_for_information": v_earth}
    runs["4: reference"] = reference_run

    # the predictions of the pre-registration, one flag each
    get = lambda name: cases[name]  # noqa: E731
    a1, b1 = get("1: Earth-moon, own frame; A (absolute)"), get("1: Earth-moon, own frame; B (nearest neighbour)")
    a2, b2 = get("2: Earth-moon, plus 29780 m per s; A (absolute)"), get("2: Earth-moon, plus 29780 m per s; B (nearest neighbour)")
    a3, b3 = get("3: two protons, plus 1e6 m per s; A (absolute)"), get("3: two protons, plus 1e6 m per s; B (nearest neighbour)")
    b3own = get("3: two protons, own frame; B (nearest neighbour)")
    a4, b4 = get("4: Sun-Earth-moon; A (absolute)"), get("4: Sun-Earth-moon; B (nearest neighbour)")
    cases["predictions"] = {
        "1: B takes the steps of A within 1%": bool(abs(b1["steps"] / a1["steps"] - 1) < 0.01),
        "2: A takes about 29 times more steps when boosted (20 to 40)": bool(20 < a2["steps"] / a1["steps"] < 40),
        "2: B takes the same steps and error boosted or not": bool(abs(b2["steps"] / b1["steps"] - 1) < 1e-3
                                                                   and abs(b2["period_error"] - b1["period_error"]) < 1e-8),
        "3: A boosted takes more than ten times the steps": bool(a3["steps"] > 10 * b3own["steps"]),
        "3: B boosted keeps steps and the 3.8e-7 error": bool(abs(b3["steps"] / b3own["steps"] - 1) < 1e-3
                                                              and abs(b3["separation_error"] - b3own["separation_error"]) < 5e-8),
        "4: A takes about 180,000 steps (120,000 to 260,000)": bool(120_000 < a4["steps"] < 260_000),
        "4: B takes 6,300 to 13,000 steps": bool(6_300 <= b4["steps"] <= 13_000),
        "4: A and B agree with the reference to 1e-5": bool(a4["separation_vs_reference"] < 1e-5 and b4["separation_vs_reference"] < 1e-5),
    }
    cases["predictions"]["pass"] = all(cases["predictions"].values())
    for name, case in cases.items():
        case.setdefault("pass", True)  # measurements carry no criterion of their own; the predictions do
    return {"id": "Q4", "pass": cases["predictions"]["pass"], "cases": cases, "runs": runs}


if __name__ == "__main__":
    outcome = q4()
    folder = write_gate_result(outcome, producer=PRODUCER)
    failed = [name for name, held in outcome["cases"]["predictions"].items() if name != "pass" and not held]
    print(f"Q4: {'every prediction holds' if outcome['pass'] else 'PREDICTIONS THAT FAILED: ' + '; '.join(failed)}; results in {folder}")
