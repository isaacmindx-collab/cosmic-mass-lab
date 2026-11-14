"""Q1 to Q3: open questions of the MVP, run against their alternatives.

Pre-registration: team/notes/Q.md (committed before any code or run).
  Q1  does L1a obey Newton's third law, for each choice of its terms?
  Q2  which energy does L1a conserve: the L0 energy (A), or the same sum read with L1a (B)?
  Q3  does the value of K (CODATA 2018 or 2022) change any verdict?
L1a is a hypothesis (decision D1). Candidate B of Q2 is not in the compendium: it is tested
here and is NOT part of the engine (it needs the physics lead's approval).

    python scenarios/Q/run.py            # all three, writes results/Q1/ ... results/Q3/
    python scenarios/Q/run.py 2          # only Q2
"""

import math
import sys

import numpy as np

from cosmicmass.constants import SI, Constants, scaled
from cosmicmass.fields import DirectSum
from cosmicmass.frame import Frame
from cosmicmass.gates.t0 import _escape_radius, write_gate_result
from cosmicmass.gates.t9 import STANDARD_GRAVITY
from cosmicmass.laws import LawSpec, make_law, third_law_residual
from cosmicmass.matter import CosmicMass, preset
from cosmicmass.runner import run
from cosmicmass.state import State

PRODUCER = "Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz)"
PHI = 79.86
TERMS = ("all", "s q g", "-m E/s", "-2 cos q E")


def _stamp_settings(scenario, law, bodies, units="SI", phi=PHI, numerics=None) -> dict:
    return {"scenario": scenario, "universe": {"phi_bar_deg": phi, "dimension": 2, "units": units}, "law": law,
            "bodies": bodies, "numerics": {"softening": 0.0, "steps": 0, **(numerics or {})},
            "kind": "mathematics", "preregistered": True}


# ---------------------------------------------------------------------------------- Q1
def q1() -> dict:
    """Newton's third law for L0 and for L1a with each choice of terms."""
    frame, solver = Frame.si(PHI), DirectSum(constants=SI)
    earth, p, e, n = preset("Earth"), preset("proton"), preset("electron"), preset("neutron")
    pairs = {"proton, electron": (p, e, 1e-10), "proton, neutron": (p, n, 1e-10), "two protons": (p, p, 1e-10),
             "Earth, proton": (earth, p, 7e6)}
    cases, runs = {}, {}
    for pair_name, (a, b, r) in pairs.items():
        state = State.from_bodies([a, b], [[0.0, 0.0], [r, 0.0]])
        laws = [("L0", LawSpec())] + [(f"L1a, {terms}", LawSpec(reading="L1a", terms=terms)) for terms in TERMS]
        for law_name, spec in laws:
            law = make_law(spec)
            out = third_law_residual(law, state, solver, frame)
            # the Composer forces alone: the total force can hide a small asymmetry under the rounding of a
            # large symmetric part (see "Changes to the plan" in team/notes/Q.md)
            composer = law.forces(state, solver.at_bodies(state), frame).composer
            composer_residual = float(np.linalg.norm(composer[0] + composer[1]))
            # prediction of the pre-registration: the residual of the two halves of the Coupling term alone
            asym = frame.s * SI.G_N * abs(a.q * b.m - b.q * a.m) / r**2
            predicted = asym if spec.terms in ("s q g", "-m E/s") else 0.0
            resolvable = predicted > 1e-13 * out["force"]  # can the total force show the predicted residual?
            case = {"largest_force": out["force"], "residual": out["residual"], "relative_residual": out["relative"],
                    "composer_residual": composer_residual, "predicted_residual": predicted,
                    "predicted_residual_visible_in_the_total_force": bool(resolvable),
                    "obeys_third_law": bool(predicted == 0.0 and out["relative"] < 1e-12)}
            if predicted:  # the Composer residual must equal the prediction; the total too, where it can show it
                agrees = abs(composer_residual - predicted) <= 1e-9 * predicted
                agrees = agrees and (not resolvable or abs(out["residual"] - predicted) <= 1e-6 * predicted)
            else:
                agrees = out["relative"] < 1e-12 and composer_residual <= 1e-12 * max(float(np.abs(composer).max()), 1e-300)
            case["pass"] = bool(agrees)  # pass = the prediction of the pre-registration holds
            cases[f"{pair_name}; {law_name}"] = case
        runs[pair_name] = _stamp_settings("Q1", LawSpec(reading="L1a").to_dict(),
                                          [{"name": a.name, "m": a.m, "q": a.q, "x": [0.0, 0.0]},
                                           {"name": b.name, "m": b.m, "q": b.q, "x": [r, 0.0]}])
    return {"id": "Q1", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


# ---------------------------------------------------------------------------------- Q2
def candidate_energies(result, frame: Frame, constants: Constants, strength: float, softening: float):
    """Candidates A and B along a run, from the positions and velocities of its time series.
    A = kinetic - G sum Re(mu_a mu_b) / r;  B = kinetic - G sum [Re + lambda s Com](mu_a mu_b) / r."""
    state, rows = result.state, result.timeseries
    n, d = state.n, state.dimension
    m, q, s = state.m, state.q, frame.s
    re = np.outer(m, m) - s * s * np.outer(q, q)  # Re(mu_a mu_b)
    com = np.outer(m, q) + np.outer(q, m) + 2 * s * frame.cos_phi() * np.outer(q, q)  # Com(mu_a mu_b)
    upper = np.triu_indices(n, k=1)
    a_values, b_values = [], []
    for row in rows:
        x = np.array([[row[f"x{i}_{k}"] for k in range(d)] for i in range(n)])
        v = np.array([[row[f"v{i}_{k}"] for k in range(d)] for i in range(n)])
        diff = x[:, None, :] - x[None, :, :]
        dist = np.sqrt(np.einsum("abd,abd->ab", diff, diff) + softening**2)[upper]
        kinetic = 0.5 * np.sum(m * np.sum(v * v, axis=1))
        a_values.append(kinetic - constants.G_N * np.sum(re[upper] / dist))
        b_values.append(kinetic - constants.G_N * np.sum((re[upper] + strength * s * com[upper]) / dist))
    return np.array(a_values), np.array(b_values)


def _drifts(values) -> dict:
    change = np.abs(values / values[0] - 1)
    return {"end_drift": float(change[-1]), "largest_excursion": float(change.max())}


def q2() -> dict:
    """Energy candidates A and B under L1a with all terms, on four runs."""
    p, e = preset("proton"), preset("electron")
    r0 = 5.29177e-11
    k = SI.G_N * p.m * e.m - SI.K * p.q * e.q
    total, reduced = p.m + e.m, p.m * e.m / (p.m + e.m)
    speed, period = math.sqrt(k / (reduced * r0)), 2 * math.pi * math.sqrt(reduced * r0**3 / k)
    pair = [{"preset": "proton", "x": [-e.m / total * r0, 0.0], "v": [0.0, -e.m / total * speed]},
            {"preset": "electron", "x": [p.m / total * r0, 0.0], "v": [0.0, p.m / total * speed]}]
    rng = np.random.default_rng(7)
    cloud = [{"name": f"body {i}", "m": 1.0, "q": float(rng.normal(0.0, 0.5)), "x": [float(c) for c in rng.uniform(-2, 2, 2)]}
             for i in range(12)]
    orbit = {"softening": 0.0, "t_end": 5 * period, "record_every": 5}
    setups = {
        "i: pair, lambda = 1": (pair, {"id": "L1a", "lambda": 1.0}, "SI", PHI, orbit),
        "ii: pair, lambda = 0.3, sign -": (pair, {"id": "L1a", "lambda": 0.3, "sign": "-"}, "SI", PHI, orbit),
        "iii: pair, lambda = 1, 120 deg": (pair, {"id": "L1a", "lambda": 1.0}, "SI", 120.0, orbit),
        "iv: 12 bodies, lambda = 0.2": (cloud, {"id": "L1a", "lambda": 0.2}, "scaled", PHI, {"steps": 3000, "record_every": 5}),
    }
    cases, runs = {}, {}
    for name, (bodies, law, units, phi, numerics) in setups.items():
        settings = {"scenario": "Q2", "universe": {"phi_bar_deg": phi, "dimension": 2, "units": units}, "law": law,
                    "bodies": bodies, "numerics": numerics, "kind": "mathematics", "preregistered": True}
        result = run(settings, out_root=None)
        frame = Frame.si(phi) if units == "SI" else Frame.scaled(phi)
        strength = make_law(LawSpec.from_dict(law)).strength(frame)
        a_values, b_values = candidate_energies(result, frame, SI if units == "SI" else scaled(), strength,
                                                result.stamp["numerics"]["softening"])
        a, b = _drifts(a_values), _drifts(b_values)
        engine_a = abs(a_values[-1] / result.summary["final"]["energy_re"] - 1)  # A must be the engine's own L0 energy
        case = {"A_L0_energy": a, "B_energy_read_with_L1a": b, "steps": result.summary["steps"],
                "A_agrees_with_the_engine_energy": float(engine_a), "signed_strength": float(strength),
                "momentum_drift": result.summary["conservation"]["momentum"]}
        case["B_conserved"] = bool(b["end_drift"] < 1e-6 and b["largest_excursion"] < 1e-5)
        case["A_conserved"] = bool(a["end_drift"] < 1e-6 and a["largest_excursion"] < 1e-5)
        case["pass"] = bool(case["B_conserved"] and not case["A_conserved"] and engine_a < 1e-9)  # the prediction
        cases[name], runs[name] = case, result
    return {"id": "Q2", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


# ---------------------------------------------------------------------------------- Q3
def _quantities(c: Constants) -> dict:
    """The numbers behind T0.1b, T0.1c, T9.1 and T9.3 for one set of constants."""
    frame, p, e, n = Frame.from_degrees(c.s, PHI), preset("proton"), preset("electron"), preset("neutron")
    strength = lambda a, b: c.G_N * a.m * b.m - c.K * a.q * b.q  # noqa: E731
    r0, reduced = 5.29177e-11, p.m * e.m / (p.m + e.m)
    bohr_period = 2 * math.pi * math.sqrt(reduced * r0**3 / strength(p, e))
    k_pp, mu_pp, d0 = strength(p, p), p.m / 2, 1e-10
    escape = _escape_radius(5.711813942831563e-15, d0, k_pp, mu_pp)  # the end time of the stored T0.1c run
    state = State.from_bodies([p, n], [[0.0, 0.0], [1e-10, 0.0]], fixed=[True, False])
    fields = DirectSum(constants=c).at_bodies(state)
    force = make_law(LawSpec(reading="L1a")).forces(state, fields, frame).composer[1]
    E = -frame.s**2 * fields.e[1]
    q_eff = float(np.dot(force, E) / np.dot(E, E)) / c.e
    return {"K": c.K, "s": c.s, "T0.1b_period": bohr_period, "T0.1c_separation": escape, "T9.1_q_eff_in_e": q_eff,
            "T9.3_field": c.s * STANDARD_GRAVITY}


def q3() -> dict:
    """The value of K: CODATA 2022 (the engine's) against CODATA 2018 (the table of docs/05)."""
    k2018 = Constants(G_N=SI.G_N, K=8.9875517923e9, c=SI.c, e=SI.e, units="SI")
    new, old = _quantities(SI), _quantities(k2018)
    verdict = lambda q: {  # noqa: E731  (the criteria of T0.1b, T9.1, T9.3)
        "T0.1b": abs(q["T0.1b_period"] / 1.5198e-16 - 1) < 1e-3,
        "T9.1": abs(abs(q["T9.1_q_eff_in_e"]) - 9.0e-19) < 0.05e-19,
        "T9.3": abs(q["T9.3_field"] - 1.14e11) < 0.005e11}
    cases = {}
    for key in new:
        change = abs(old[key] / new[key] - 1)
        cases[key] = {"codata_2022": new[key], "codata_2018": old[key], "relative_change": change, "pass": bool(change < 1e-8)}
    flips = {name: verdict(new)[name] != verdict(old)[name] for name in verdict(new)}
    cases["verdicts"] = {"with_codata_2022": verdict(new), "with_codata_2018": verdict(old), "any_flip": any(flips.values()),
                         "pass": bool(not any(flips.values()))}
    runs = {"reference": _stamp_settings("Q3", {"id": "L0"}, [{"preset": "proton", "x": [0.0, 0.0]}])}
    return {"id": "Q3", "pass": all(c["pass"] for c in cases.values()), "cases": cases, "runs": runs}


if __name__ == "__main__":
    wanted = sys.argv[1:] or ["1", "2", "3"]
    for number, function in (("1", q1), ("2", q2), ("3", q3)):
        if number in wanted:
            outcome = function()
            folder = write_gate_result(outcome, producer=PRODUCER, law="L0 and the hypothesis L1a")
            failed = [name for name, case in outcome["cases"].items() if not case["pass"]]
            print(f"{outcome['id']}: {'predictions hold' if outcome['pass'] else 'PREDICTION FAILED for ' + '; '.join(failed)}; results in {folder}")
