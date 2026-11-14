"""The runner: from settings to stamped results (tasks E7.1 and E7.3).

    python -m cosmicmass run scenarios/<ID>/settings.json

`run(settings)` builds the frame, the law, the field solver, the environment and the
integrator, advances the state, measures the conservation diagnostics, and writes
`stamp.json`, `summary.json` and `timeseries.csv` (the runner writes them, never a human).

Outside the MVP: checkpoints and resuming, and repeating a step with half the time step
when a drift passes its tolerance (`ARCHITECTURE.md`, section 6).
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .constants import SI, scaled
from .diagnostics import Diagnostics, drifts
from .environment import Environment, kinetic_temperature
from .fields import DirectSum, smallest_separation
from .integrators import StepContext, VelocityVerlet
from .settings import Settings, SettingsError, load_settings, make_heat_bath, make_inflow
from .stamp import build_stamp, engine_commit, make_run_id, write_results
from .state import State

__all__ = ["run", "RunResult", "main"]

_MAX_BODIES_IN_TIMESERIES = 16


@dataclass
class RunResult:
    stamp: dict
    summary: dict
    folder: Path | None  # None when nothing was written
    state: State  # the final state
    timeseries: list


def _row(step: int, dt: float, measured: dict, state: State, bodies: bool = True, k_b: float | None = None) -> dict:
    row = {"step": step, "t": measured["t"], "dt": dt, "kinetic": measured["kinetic"],
           "energy_re": measured["energy_re"], "mass": measured["mass"], "charge": measured["charge"]}
    row.update({f"p{k}": p for k, p in enumerate(measured["momentum"])})
    if k_b is not None:  # a heat bath: the temperature of the moving bodies
        row["temperature"] = kinetic_temperature(state, k_b)
    if bodies and state.n <= _MAX_BODIES_IN_TIMESERIES:  # not with inflow: the number of bodies grows
        for i in range(state.n):
            row.update({f"x{i}_{k}": float(c) for k, c in enumerate(state.x[i])})
            row.update({f"v{i}_{k}": float(c) for k, c in enumerate(state.v[i])})
    return row


def run(settings, out_root: Path | str | None = Path("results"), now=None) -> RunResult:
    """Run a settings object, file or dictionary. With `out_root=None` nothing is written."""
    settings = settings if isinstance(settings, Settings) else load_settings(settings)
    num, universe = settings.numerics, settings.universe
    if num["steps"] is None and num["t_end"] is None:
        raise SettingsError("'numerics': give 'steps', 't_end' or both, so that the run can stop")
    if not num["adaptive"] and num["dt_initial"] is None:
        raise SettingsError("'numerics.dt_initial' is needed when 'numerics.adaptive' is false")

    constants = SI if universe["units"] == "SI" else scaled()
    state = settings.state.copy()
    softening = num["softening"]
    if softening is None:  # decision D10: a fraction of the smallest initial separation
        sep = smallest_separation(state)
        softening = float(num["softening_fraction"] * sep) if np.isfinite(sep) else 0.0
    background = None if universe["background"] == "none" else universe["background"]
    solver = DirectSum(constants=constants, softening=softening, background=background)
    box = universe.get("box") or {}
    inflow = make_inflow(universe["inflow"], box, t0=state.t) if universe.get("inflow") else None
    bath = make_heat_bath(universe["heat_bath"], universe["units"]) if universe.get("heat_bath") else None
    environment = Environment(universe["boundary"], box.get("lower"), box.get("upper"), inflow=inflow, heat_bath=bath)
    rng = np.random.default_rng(num["seed"])  # every random draw of the run (D13: the seed is in the stamp)
    columns = {"bodies": inflow is None, "k_b": bath.k_b if bath is not None else None}
    ctx = StepContext(settings.make_law(), solver, settings.frame, eta=num["eta"], dt_min=num["dt_min"],
                      speed_reference=num["speed_reference"],
                      dt_max=np.inf if num["dt_max"] is None else num["dt_max"])
    integrator = VelocityVerlet()
    diagnostics = Diagnostics(settings.frame, constants, softening, background)

    every = num.get("record_every") or (max(1, num["steps"] // 1000) if num["steps"] else 100)
    first = diagnostics.measure(state)
    rows, step, dt, wall_hits = [_row(0, 0.0, first, state, **columns)], 0, 0.0, 0
    temperatures = []  # with a heat bath: the temperature after every step
    wall_impulse = np.zeros(state.dimension)  # momentum given to the walls so far
    t_end = np.inf if num["t_end"] is None else num["t_end"]
    max_steps = np.inf if num["steps"] is None else num["steps"]
    while step < max_steps and state.t < t_end:
        dt = integrator.next_dt(state, ctx) if num["adaptive"] else num["dt_initial"]
        last_step = state.t + dt >= t_end
        dt = min(dt, t_end - state.t)
        state = integrator.step(state, dt, ctx)
        if last_step:
            state.t = float(t_end)  # end exactly on t_end
        step += 1
        events = environment.apply(state, dt, rng)
        if events:
            for event in events:
                if "wall" not in event:  # inflow and heat bath: counted by the environment
                    continue
                wall_hits += event["bodies"]
                if "absorbed" in event:  # an absorbing wall takes the whole momentum of the body
                    wall_impulse += event["absorbed"]["momentum"]
                else:
                    wall_impulse[event["wall"][0]] += event["impulse"]
            ctx.invalidate()
        if bath is not None:
            temperatures.append(kinetic_temperature(state, bath.k_b))
        if step % every == 0:
            rows.append(_row(step, dt, diagnostics.measure(state), state, **columns))
    last = diagnostics.measure(state)
    if rows[-1]["step"] != step:
        rows.append(_row(step, dt, last, state, **columns))

    with_walls = dict(last, momentum=[p + w for p, w in zip(last["momentum"], wall_impulse)])
    summary = {
        "scenario": settings.scenario,
        "law": settings.law_spec.reading,
        "steps": step,
        "t_end": last["t"],
        "initial": first,
        "final": last,
        "conservation": drifts(first, last),
        "wall_hits": wall_hits,
        "wall_impulse": [float(p) for p in wall_impulse],
        "absorbed": {"bodies": environment.collected["bodies"], "m": environment.collected["m"],
                     "q": environment.collected["q"], "alive_at_the_end": int(state.alive.sum())},
        # E6b: what entered (mass and charge drifts include it) and what the heat bath did
        "inflow": None if inflow is None else {"bodies": inflow.added, "m": inflow.added * inflow.m,
                                               "q": inflow.added * inflow.q},
        "heat_bath": None if bath is None else {
            "temperature": bath.temperature, "collisions": bath.collisions,
            "temperature_mean_second_half": float(np.mean(temperatures[len(temperatures) // 2:]))
            if temperatures else None},
        # momentum of the bodies plus the momentum they gave to the walls: conserved with reflecting walls
        "momentum_with_walls_drift": drifts(first, with_walls)["momentum"],
        "convergence": None,  # filled by the convergence helper (E8.2), not by a single run
        "verdict": "none",
        "explanation": "A plain run has no pass criterion; scenarios add their own verdict.",
    }
    commit = engine_commit()
    stamp = build_stamp(settings, softening, make_run_id(commit, now), commit)
    folder = None
    if out_root is not None:
        folder = Path(out_root) / settings.scenario / stamp["run_id"]
        write_results(folder, stamp, summary, rows)
    return RunResult(stamp, summary, folder, state, rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cosmicmass", description="The virtual universe of cosmic masses.")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run a settings file and write stamped results")
    run_parser.add_argument("settings", help="path to a settings.json file")
    run_parser.add_argument("--out", default="results", help="root folder of the results (default: results)")
    args = parser.parse_args(argv)
    try:
        result = run(args.settings, out_root=args.out)
    except (SettingsError, OSError) as exc:
        print(f"error: {exc}")
        return 2
    drift = result.summary["conservation"]
    print(f"scenario {result.summary['scenario']}, law {result.summary['law']}: "
          f"{result.summary['steps']} steps to t = {result.summary['t_end']:.6g}")
    print(f"drifts: energy (Re) {drift['energy_re']}, momentum {drift['momentum']}, "
          f"mass {drift['mass']}, charge {drift['charge']}")
    print(f"results: {result.folder}")
    return 0
