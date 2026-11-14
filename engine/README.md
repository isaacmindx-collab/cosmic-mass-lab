# Engine

Components E1-E9: tasks in `docs/WORK-PLAN.md`, modules and interface contracts in `ARCHITECTURE.md`. The package skeleton exists (P1): `pip install -e .[dev]` from the repository root, then `pytest`. Implemented so far: the algebra core E1 (`constants.py`, `frame.py`, `gn.py`, `gnarray.py`, `readings.py`, `matter.py`), the state, the law interface with the reference law L0, a minimal settings loader, the static field solver, the velocity Verlet integrator with its adaptive step, and reflecting walls.

Run a settings file from the repository root:

```bash
python -m cosmicmass run path/to/settings.json        # writes results/<scenario>/<run-id>/
python -m cosmicmass run path/to/settings.json --progress   # a line for every recorded row
python -m cosmicmass run path/to/settings.json --resume     # take up an interrupted run (see below)
```

It writes `stamp.json`, `summary.json` and `timeseries.csv` (`team/RESULTS-STANDARD.md`). The settings format is described in `engine/cosmicmass/settings.py`.

Long runs (E7.1): with `"checkpoint_every": 1000` in the `numerics` of the settings, the run writes `results/<scenario>/checkpoint.npz` every 1000 steps. Ctrl-C stops the run after the step it is in and writes the checkpoint too. `--resume` takes the run up again, and it then writes the same `summary.json` and `timeseries.csv` as a run that was never interrupted. The checkpoint is removed when the run ends; a checkpoint of other settings or of another engine commit is refused.

Long tests are marked `slow` and skipped by default; run them with `pytest -m slow`. Rule D18: every code change updates `ARCHITECTURE.md` in the same pull request.
