"""The runner: from settings to stamped results (tasks E7.1 and E7.3).

    python -m cosmicmass run scenarios/<ID>/settings.json

`run(settings)` builds the frame, the law, the field solver, the environment and the
integrator, advances the state, measures the conservation diagnostics, and writes
`stamp.json`, `summary.json` and `timeseries.csv` (the runner writes them, never a human).

Checkpoints (E7.1): with `numerics.checkpoint_every = k` the run writes a checkpoint every
`k` steps (`checkpoint.py`), and `run(..., resume=True)` or `--resume` takes it up again. A
run interrupted and resumed gives the same `summary.json` and `timeseries.csv` as a run that
was never interrupted: the checkpoint holds every value the loop carries.

Step control (`ARCHITECTURE.md`, section 6; off by default): with `numerics.drift_tolerance`
a step that changes the conserved energy by more than that relative amount is repeated with
half the time step, at most `MAX_HALVINGS` times; the repeats are counted in the summary.
"""

import argparse
import signal
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import checkpoint as checkpoints
from .checkpoint import CheckpointError
from .constants import SI, scaled
from .diagnostics import Diagnostics, drifts
from .environment import Environment, kinetic_temperature
from .fields import DirectSum, smallest_separation
from .integrators import Boris, StepContext, VelocityVerlet
from .settings import Settings, SettingsError, load_settings, make_heat_bath, make_inflow
from .stamp import ResultsError, build_stamp, engine_commit, make_run_id, t0_status, write_results
from .state import State

__all__ = ["run", "RunResult", "Interrupted", "main", "CHECKPOINT_NAME", "MAX_HALVINGS"]

_MAX_BODIES_IN_TIMESERIES = 16
CHECKPOINT_NAME = "checkpoint.npz"  # in results/<scenario>/, beside the run folders; removed when the run ends
MAX_HALVINGS = 10  # step control: a step is repeated with half the time step at most this many times


class Interrupted(Exception):
    """The run was asked to stop (`should_stop`); `checkpoint` is the file to resume from, or None."""

    def __init__(self, step: int, checkpoint: Path | None):
        self.step, self.checkpoint = step, checkpoint
        where = f"; checkpoint: {checkpoint}" if checkpoint is not None else "; no checkpoint was written"
        super().__init__(f"interrupted after step {step}{where}")


@dataclass
class RunResult:
    stamp: dict
    summary: dict
    folder: Path | None  # None when nothing was written
    state: State  # the final state
    timeseries: list


def _row(step: int, dt: float, measured: dict, state: State, bodies: bool = True, k_b: float | None = None) -> dict:
    row = {
        "step": step,
        "t": measured["t"],
        "dt": dt,
        "kinetic": measured["kinetic"],
        "energy_re": measured["energy_re"],
        "energy_total": measured.get("energy_total"),  # E9: the energy the law conserves (empty if not defined)
        "mass": measured["mass"],
        "charge": measured["charge"],
    }
    row.update({f"p{k}": p for k, p in enumerate(measured["momentum"])})
    if k_b is not None:  # a heat bath: the temperature of the moving bodies
        row["temperature"] = kinetic_temperature(state, k_b)
    if bodies and state.n <= _MAX_BODIES_IN_TIMESERIES:  # not with inflow: the number of bodies grows
        for i in range(state.n):
            row.update({f"x{i}_{k}": float(c) for k, c in enumerate(state.x[i])})
            row.update({f"v{i}_{k}": float(c) for k, c in enumerate(state.v[i])})
    return row


def _super_particles(settings) -> dict | None:
    """E5.4 (review of #66): for populations with a `weight` other than 1, the temperatures of this summary
    are per super-particle (computed with its whole mass) and must be divided by the weight to give the
    temperature of the real particles. None when no population is weighted."""
    weights = [float(p.get("weight", 1.0)) for p in settings.meta.get("populations", [])]
    if all(w == 1.0 for w in weights):
        return None
    return {
        "weights": weights,
        "note": "temperatures here use each super-particle's whole mass: divide by its population's weight "
        "for the temperature of the real particles; motion and wall pressure are not affected",
    }


def wall_pressure(box: dict, load: dict, elapsed: float) -> dict | None:
    """E8.1: the pressure on the walls of a box, from the momentum they took over `elapsed`
    (`docs/05`, T6.1: "pressure from Re momentum flux on the walls"). Each wall: its momentum
    divided by the time and by its size (a length in 2D, an area in 3D); and the mean over the
    whole boundary. In 2D (bodies moving in a plane, D21) it is a force per unit length, to be
    compared with `n k T` for `n` per unit area. None without a box or without time."""
    if not box or elapsed <= 0:
        return None
    extent = np.subtract(box["upper"], box["lower"]).astype(float)
    d = len(extent)
    faces = {}
    for axis in range(d):
        others = np.delete(extent, axis)
        faces[axis] = float(np.prod(others))  # 2D: the length of the wall; 3D: its area
    per_wall = {}
    for axis in range(d):
        for side in ("lower", "upper"):
            key = f"{axis}-{side}"
            per_wall[key] = load.get(key, 0.0) / (elapsed * faces[axis])
    boundary = 2 * sum(faces.values())
    total = sum(load.values())
    return {"momentum": {k: load.get(k, 0.0) for k in per_wall}, "pressure": per_wall,
            "pressure_mean": total / (elapsed * boundary), "elapsed": elapsed}  # fmt: skip


def _conserved(measured: dict):
    """The energy the step control watches: the energy the law conserves (E9), or the Real energy."""
    return measured["energy_re"] if measured.get("energy_total") is None else measured["energy_total"]


def _beyond(before: float, after: float, tolerance: float) -> bool:
    return abs(after - before) > tolerance * abs(before) if before != 0 else False  # no scale: nothing to compare


def run(
    settings,
    out_root: Path | str | None = Path("results"),
    now=None,
    *,
    resume: bool | Path | str = False,
    checkpoint: Path | str | None = None,
    progress=None,
    should_stop=None,
) -> RunResult:
    """Run a settings object, file or dictionary. With `out_root=None` nothing is written.

    `checkpoint`: where checkpoints go (default `<out_root>/<scenario>/checkpoint.npz`); they are
    written every `numerics.checkpoint_every` steps and when `should_stop()` says so, and the file
    is removed when the run ends. `resume`: True (from that file) or a path. `progress`: called
    with every row of the time series as it is recorded. `should_stop`: called after every step;
    when it returns True the run writes a checkpoint and raises `Interrupted`."""
    settings = settings if isinstance(settings, Settings) else load_settings(settings)
    num, universe = settings.numerics, settings.universe
    if num["steps"] is None and num["t_end"] is None:
        raise SettingsError("'numerics': give 'steps', 't_end' or both, so that the run can stop")
    if not num["adaptive"] and num["dt_initial"] is None:
        raise SettingsError("'numerics.dt_initial' is needed when 'numerics.adaptive' is false")
    checkpoint_every, tolerance = num.get("checkpoint_every"), num.get("drift_tolerance")

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
    ctx = StepContext(
        settings.make_law(),
        solver,
        settings.frame,
        eta=num["eta"],
        dt_min=num["dt_min"],
        speed_reference=num["speed_reference"],
        dt_max=np.inf if num["dt_max"] is None else num["dt_max"],
    )
    integrator = Boris() if num["integrator"] == "boris" else VelocityVerlet()
    diagnostics = Diagnostics(settings.frame, constants, softening, background, law=ctx.law)  # E9: Composer energy

    commit = engine_commit()
    # which run a checkpoint belongs to: the stamp and the initial state
    identity = checkpoints.run_key(build_stamp(settings, softening, "", commit), state)
    if checkpoint is not None:
        checkpoint = Path(checkpoint)
    elif out_root is not None and (checkpoint_every or resume or should_stop is not None):
        checkpoint = Path(out_root) / settings.scenario / CHECKPOINT_NAME
    every = num.get("record_every") or (max(1, num["steps"] // 1000) if num["steps"] else 100)
    retries = {"repeated": 0, "gave_up": 0}  # step control: steps repeated with half the step
    resumed = []  # the steps at which this run was taken up again (in the stamp)
    if resume:
        source = checkpoint if resume is True else Path(resume)
        if source is None:
            raise CheckpointError("nothing to resume from: give a checkpoint path, or an output folder")
        state, cache, saved, book = checkpoints.load(source, identity)
        if cache is not None:  # the acceleration remembered for this state (computed with the half-step velocity)
            ctx._cache = (state, *cache)
        first, rows, step, dt, wall_hits = book["first"], book["rows"], book["step"], book["dt"], book["wall_hits"]
        wall_load, retries, resumed = book["wall_load"], book["retries"], book["resumed"] + [book["step"]]
        wall_impulse, temperatures = saved["wall_impulse"], [float(t) for t in saved["temperatures"]]
        environment.collected.update(book["collected"], momentum=saved.get("collected_momentum"))
        if inflow is not None:
            inflow.added = book["inflow_added"]
        if bath is not None:
            bath.collisions = book["bath_collisions"]
        rng.bit_generator.state = book["rng"]
    else:
        first = diagnostics.measure(state)
        rows, step, dt, wall_hits = [_row(0, 0.0, first, state, **columns)], 0, 0.0, 0
        temperatures = []  # with a heat bath: the temperature after every step
        wall_impulse = np.zeros(state.dimension)  # momentum given to the walls so far
        wall_load = {}  # E8.1: the size of the momentum each wall took, for the pressure

    def write_checkpoint() -> None:
        arrays = {"wall_impulse": wall_impulse, "temperatures": np.array(temperatures, dtype=float)}
        if environment.collected["momentum"] is not None:
            arrays["collected_momentum"] = environment.collected["momentum"]
        book = {
            "step": step,
            "dt": dt,
            "wall_hits": wall_hits,
            "wall_load": wall_load,
            "rows": rows,
            "first": first,
            "retries": retries,
            "resumed": resumed,
            "collected": {k: v for k, v in environment.collected.items() if k != "momentum"},
            "inflow_added": None if inflow is None else inflow.added,
            "bath_collisions": None if bath is None else bath.collisions,
            "rng": rng.bit_generator.state,
        }
        checkpoints.save(checkpoint, identity, state, ctx._cache, arrays, book)

    t_end = np.inf if num["t_end"] is None else num["t_end"]
    max_steps = np.inf if num["steps"] is None else num["steps"]
    while step < max_steps and state.t < t_end:
        dt = integrator.next_dt(state, ctx) if num["adaptive"] else num["dt_initial"]
        if tolerance is None:
            last_step = state.t + dt >= t_end
            dt = min(dt, t_end - state.t)
            state = integrator.step(state, dt, ctx)
        else:  # step control: repeat the step with half the time step while the energy changes too much
            ctx.acceleration(state)
            remembered, before = ctx._cache, _conserved(diagnostics.measure(state))
            for halving in range(MAX_HALVINGS + 1):
                last_step = state.t + dt >= t_end
                dt = min(dt, t_end - state.t)
                new = integrator.step(state, dt, ctx)
                if not _beyond(before, _conserved(diagnostics.measure(new)), tolerance):
                    break
                if halving == MAX_HALVINGS:
                    retries["gave_up"] += 1  # kept as it is, and counted
                    break
                retries["repeated"] += 1
                ctx._cache, dt = remembered, 0.5 * dt
            state = new
        if last_step:
            state.t = float(t_end)  # end exactly on t_end
        step += 1
        events = environment.apply(state, dt, rng)
        if events:
            for event in events:
                if "wall" not in event:  # inflow and heat bath: counted by the environment
                    continue
                wall_hits += event["bodies"]
                axis, side = event["wall"]
                if "absorbed" in event:  # an absorbing wall takes the whole momentum of the body
                    wall_impulse += event["absorbed"]["momentum"]
                else:
                    wall_impulse[axis] += event["impulse"]
                key = f"{axis}-{side}"
                wall_load[key] = wall_load.get(key, 0.0) + abs(event["impulse"])
            ctx.invalidate()
        if bath is not None:
            temperatures.append(kinetic_temperature(state, bath.k_b))
        if step % every == 0:
            rows.append(_row(step, dt, diagnostics.measure(state), state, **columns))
            if progress is not None:
                progress(rows[-1])
        if checkpoint is not None and checkpoint_every and step % checkpoint_every == 0:
            write_checkpoint()
        if should_stop is not None and should_stop():
            if checkpoint is not None:
                write_checkpoint()
            raise Interrupted(step, checkpoint)
    last = diagnostics.measure(state)
    if rows[-1]["step"] != step:
        rows.append(_row(step, dt, last, state, **columns))
        if progress is not None:
            progress(rows[-1])

    with_walls = dict(last, momentum=[p + w for p, w in zip(last["momentum"], wall_impulse)])
    summary = {
        "scenario": settings.scenario,
        "law": settings.law_spec.reading,
        "steps": step,
        "t_end": last["t"],
        "stopped_by": "t_end" if state.t >= t_end else "steps",
        "initial": first,
        "final": last,
        "conservation": drifts(first, last),
        "wall_hits": wall_hits,
        "wall_impulse": [float(p) for p in wall_impulse],
        "walls": wall_pressure(box, wall_load, last["t"] - first["t"]),
        "super_particles": _super_particles(settings),
        "absorbed": {
            "bodies": environment.collected["bodies"],
            "m": environment.collected["m"],
            "q": environment.collected["q"],
            "alive_at_the_end": int(state.alive.sum()),
        },
        # E6b: what entered (mass and charge drifts include it) and what the heat bath did
        "inflow": None
        if inflow is None
        else {"bodies": inflow.added, "m": inflow.added * inflow.m, "q": inflow.added * inflow.q},
        "heat_bath": None
        if bath is None
        else {
            "temperature": bath.temperature,
            "collisions": bath.collisions,
            "temperature_mean_second_half": float(np.mean(temperatures[len(temperatures) // 2 :]))
            if temperatures
            else None,
        },
        # momentum of the bodies plus the momentum they gave to the walls: conserved with reflecting walls
        "momentum_with_walls_drift": drifts(first, with_walls)["momentum"],
        # step control (numerics.drift_tolerance): steps repeated with half the step, and steps kept beyond it
        "step_control": None if tolerance is None else {"drift_tolerance": tolerance, **retries},
        "convergence": None,  # filled by the convergence helper (E8.2), not by a single run
        "verdict": "none",
        "explanation": "A plain run has no pass criterion; scenarios add their own verdict.",
    }
    stamp = build_stamp(settings, softening, make_run_id(commit, now), commit, t0_status(commit))
    if resumed:
        stamp["resumed_at_steps"] = resumed
    folder = None
    if out_root is not None:
        folder = Path(out_root) / settings.scenario / stamp["run_id"]
        write_results(folder, stamp, summary, rows)
    if checkpoint is not None:
        checkpoint.unlink(missing_ok=True)  # the run is whole: nothing left to resume
    return RunResult(stamp, summary, folder, state, rows)


def _progress_line(row: dict) -> None:
    print(f"step {row['step']}: t = {row['t']:.6g}, dt = {row['dt']:.3g}, energy (Re) = {row['energy_re']:.12g}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m cosmicmass", description="The virtual universe of cosmic masses.")
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="run a settings file and write stamped results")
    run_parser.add_argument("settings", help="path to a settings.json file")
    run_parser.add_argument("--out", default="results", help="root folder of the results (default: results)")
    run_parser.add_argument(
        "--resume",
        nargs="?",
        const=True,
        default=False,
        metavar="CHECKPOINT",
        help="take up an interrupted run from its checkpoint (default: <out>/<scenario>/checkpoint.npz)",
    )
    run_parser.add_argument("--progress", action="store_true", help="print a line for every recorded row")
    args = parser.parse_args(argv)
    asked = []  # Ctrl-C asks the run to stop after the step it is in, so that it can write a checkpoint
    try:
        previous = signal.signal(signal.SIGINT, lambda *_: asked.append(True))
    except ValueError:  # not in the main thread: Ctrl-C stays as it is
        previous = None
    try:
        result = run(
            args.settings,
            out_root=args.out,
            resume=args.resume,
            progress=_progress_line if args.progress else None,
            should_stop=(lambda: bool(asked)) if previous is not None else None,
        )
    except Interrupted as exc:
        print(f"{exc}")
        if exc.checkpoint is not None:
            print(f"resume with: python -m cosmicmass run {args.settings} --out {args.out} --resume")
        return 130
    except (SettingsError, CheckpointError, ResultsError, OSError) as exc:
        print(f"error: {exc}")
        return 2
    finally:
        if previous is not None:
            signal.signal(signal.SIGINT, previous)
    drift = result.summary["conservation"]
    print(
        f"scenario {result.summary['scenario']}, law {result.summary['law']}: "
        f"{result.summary['steps']} steps to t = {result.summary['t_end']:.6g}"
    )
    print(
        f"drifts: energy (Re) {drift['energy_re']}, energy (total, E9) {drift.get('energy_total')}, "
        f"momentum {drift['momentum']}, "
        f"mass {drift['mass']}, charge {drift['charge']}"
    )
    print(f"results: {result.folder}")
    return 0
