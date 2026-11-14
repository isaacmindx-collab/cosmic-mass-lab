"""The settings stamp and the files of a run (task E7.2; `team/RESULTS-STANDARD.md`).

Every run writes, into `results/<ID>/<run-id>/`: `stamp.json` (who, what, with which
settings and which engine commit), `summary.json` (the measured quantities and the
verdict; the same stamp on the same commit gives the same file) and `timeseries.csv`.
"""

import csv
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import mpmath
import numpy
import sympy

__all__ = ["engine_commit", "make_run_id", "build_stamp", "write_results"]


def engine_commit() -> str:
    """Short commit of the engine, with "-dirty" if files are changed; "unknown" outside git."""
    here = Path(__file__).resolve().parent
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"], cwd=here, capture_output=True, text=True, check=True
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=here,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        return commit + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def make_run_id(commit: str, now: datetime | None = None) -> str:
    """`YYYYMMDD-HHMMSS-<short engine commit>` (UTC)."""
    now = datetime.now(timezone.utc) if now is None else now
    return f"{now:%Y%m%d-%H%M%S}-{commit}"


def build_stamp(settings, softening: float, run_id: str, commit: str, t0_status: str = "not run") -> dict:
    """The stamp of `team/RESULTS-STANDARD.md`, section 2."""
    matter = {}
    for body in settings.bodies:
        key = (body.name, body.m, body.q)
        matter[key] = matter.get(key, 0) + 1
    numerics = {**settings.numerics, "softening": softening}
    universe = {k: settings.universe[k] for k in ("phi_bar_deg", "dimension", "units", "boundary", "background")}
    for key in ("box", "inflow", "heat_bath"):
        if settings.universe.get(key) is not None:
            universe[key] = settings.universe[key]
    return {
        "scenario": settings.scenario,
        "run_id": run_id,
        "engine_commit": commit,
        "t0_status": t0_status,
        "law": settings.law_spec.to_dict(),
        "universe": universe,
        "matter": [{"name": name, "m": m, "q": q, "n": n} for (name, m, q), n in matter.items()],
        "numerics": numerics,
        "environment": {
            "python": platform.python_version(),
            "sympy": sympy.__version__,
            "mpmath": mpmath.__version__,
            "numpy": numpy.__version__,
        },
        "kind": settings.meta["kind"],
        "preregistered": settings.meta["preregistered"],
        "producer": settings.meta["producer"],
    }


def write_results(folder: Path, stamp: dict, summary: dict, rows: list) -> None:
    """Write `stamp.json`, `summary.json` and `timeseries.csv` into a new folder."""
    folder.mkdir(parents=True, exist_ok=False)
    for name, data in (("stamp.json", stamp), ("summary.json", summary)):
        (folder / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with open(folder / "timeseries.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
