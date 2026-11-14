"""Bridge between the web universe and the engine (task UI1).

Runs inside the browser (Pyodide, Python 3.12). It calls the verified engine
`cosmicmass` unchanged: every number shown on the page comes from `cosmicmass.runner.run`.
Nothing is written to disk; the trajectory is returned to the page as JSON.
"""

import json

import numpy as np

import cosmicmass
import cosmicmass.runner as runner
from cosmicmass.matter import PRESETS

# In the browser there is no git: the stamp names the release instead of a commit.
runner.engine_commit = lambda: f"web-v{cosmicmass.__version__}"

MAX_FRAMES = 1500  # frames sent to the page


def presets() -> str:
    """The matter presets of the engine, for the page's body editor."""
    return json.dumps({name: {"m": b.m, "q": b.q} for name, b in PRESETS.items()})


def run_scene(settings_json: str) -> str:
    """Run one settings dictionary; return trajectory, drifts and stamp as JSON."""
    settings = json.loads(settings_json)
    result = runner.run(settings, out_root=None)
    rows = result.timeseries
    n = len(settings["bodies"])
    keep = max(1, -(-len(rows) // MAX_FRAMES))
    picked = rows[::keep] if rows[::keep][-1] is rows[-1] else rows[::keep] + [rows[-1]]
    t = [r["t"] for r in picked]
    paths = [[[r[f"x{i}_0"], r[f"x{i}_1"]] for r in picked] for i in range(n)]
    energy = np.array([r["energy_re"] for r in rows])
    excursion = float(np.max(np.abs(energy / energy[0] - 1))) if energy[0] != 0 else None
    summary = result.summary
    return json.dumps(
        {
            "t": t,
            "paths": paths,
            "steps": summary["steps"],
            "t_end": summary["t_end"],
            "drift": summary["conservation"],
            "energy_excursion": excursion,
            "law": summary["law"],
            "stamp": result.stamp,
            "version": cosmicmass.__version__,
        },
        default=float,
    )
