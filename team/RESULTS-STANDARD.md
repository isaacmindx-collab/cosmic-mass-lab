# Results standard

Every result in the project follows this standard, so that anyone can re-run it and get the same numbers. Changes to this file go through the verification lead (`TEAM.md`, section 2.2).

## 1. Folder layout

```
engine/                     the engine (E1-E4): algebra, field solver, integrator, law plug-ins
scenarios/<ID>/run.py       the script of one scenario (for example scenarios/T1.4/run.py)
scenarios/<ID>/settings.json  its default settings
results/<ID>/<run-id>/      outputs of one run (written by run.py, never by hand)
  stamp.json                the settings stamp (section 2)
  summary.json              the measured quantities and the verdict
  timeseries.csv            optional: quantities over time
  figures/                  optional: plots, each regenerable from the data
team/notes/<ID>.md          the notebook (pre-registration, progress, results, handoff)
```

`<run-id>` is `YYYYMMDD-HHMMSS-<short engine commit>`.

## 2. The settings stamp (`stamp.json`)

Every run writes a stamp with at least:

```json
{
  "scenario": "T1.4",
  "run_id": "20261112-143005-ab12cd3",
  "engine_commit": "ab12cd3",
  "t0_status": "pass",
  "law": {"id": "L1e", "sign": "+", "lambda": 1.0, "direction": "radial",
          "terms": "all", "B_cal": "off", "inertia": "Re", "range": "1/r^2"},
  "universe": {"phi_bar_deg": 79.86, "dimension": 2, "units": "SI",
               "boundary": "open", "background": "none"},
  "matter": [{"name": "electron", "m": 9.1093837e-31, "q": -1.602176634e-19, "n": 1}],
  "numerics": {"integrator": "verlet", "dt_initial": 1e-19, "adaptive": true,
               "softening": 5.3e-14, "steps": 100000, "seed": 12345},
  "environment": {"python": "3.12", "sympy": "1.14.0", "mpmath": "1.3.0", "numpy": "x.y.z"},
  "kind": "finding",
  "preregistered": true,
  "producer": "@handle or agent/model (sponsor @handle)"
}
```

`kind` is one of `mathematics`, `measurement-check` or `finding`. `preregistered` is false for exploratory runs.

Written by the engine since E7 (`team/notes/E7.md`; questions 26 and 27 of `team/QUESTIONS.md`):

- `t0_status` is `pass`, `fail` or `not run`: the verdict of the stored T0.1 to T0.5 runs made on the same engine code as this run.
- `resumed_at_steps` (only when it applies): the steps at which the run was taken up again from a checkpoint. A resumed run gives the same `summary.json` as a run never interrupted.
- `numerics` may hold `checkpoint_every` (it does not change the result) and `drift_tolerance` (step control; it does, and belongs in the pre-registration of a scenario that uses it).
- The stamp and the summary are checked against `engine/schemas/` before they are written.

## 3. Determinism

- Every random draw comes from a seeded generator, with the seed in the stamp.
- The same stamp on the same engine commit must give the same `summary.json`: bit-for-bit where possible, otherwise within the stated tolerance.
- Pinned environment: `requirements.txt` at the repository root. Record any deviation in the stamp.

## 4. Required measurements in `summary.json`

- the quantities named in the scenario's pass criteria;
- conservation: the relative drift of total mass, total charge, energy (`Re` and `Com`) and momentum over the run;
- convergence: the same quantities at `dt/2` and `dt/4`, and at a smaller and a larger particle count, with the relative changes;
- the verdict: `pass`, `fail` or `finding`, with one sentence of explanation.

## 5. Tolerances

| Check | Default tolerance |
|---|---|
| T0 against analytic references | 0.1% for orbital periods; 1e-6 relative for forces |
| conservation of mass and charge | exact (integer counts or 1e-12 relative) |
| conservation of energy and momentum | relative drift < 1e-6 over the run, unless the scenario states otherwise |
| convergence | change < 1% between `dt/2` and `dt/4`, and between particle counts |
| reproduction by a reviewer | same `summary.json` within the tolerances above |

A scenario may tighten these. Loosening needs a decision (`TEAM.md`, section 2.2).

## 6. Figures

- Every figure is regenerable from the data in the same results folder, by a script in `scenarios/<ID>/`.
- Axes are labelled with units. The reading (`Re`, `Com`, `Sh`, `Ht`, `abs`) and the law are in the caption.
