"""The settings stamp and the files of a run (task E7.2; `team/RESULTS-STANDARD.md`).

Every run writes, into `results/<ID>/<run-id>/`: `stamp.json` (who, what, with which
settings and which engine commit), `summary.json` (the measured quantities and the
verdict; the same stamp on the same commit gives the same file) and `timeseries.csv`.

Before they are written, the stamp and the summary are checked against the P4 schemas
(`engine/schemas/`): a file that breaks the standard is never written. The check needs the
package `jsonschema` (a development dependency, D24) and the schema files of a source
checkout; where either is missing it is skipped, and `tools/validate_results.py` in CI
remains the check.

`t0_status()` answers the stamp's question "did the consistency gate T0 pass on this engine?"
from the stored results of T0.1 to T0.5 and git.
"""

import csv
import json
import platform
import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

import mpmath
import numpy
import sympy

__all__ = [
    "engine_commit",
    "make_run_id",
    "build_stamp",
    "write_results",
    "t0_status",
    "validate_outputs",
    "ResultsError",
    "T0_TESTS",
]

T0_TESTS = ("T0.1", "T0.2", "T0.3", "T0.4", "T0.5")  # the consistency gate (docs/05; gates/t0.py)
_PACKAGE = Path(__file__).resolve().parent
_SCHEMAS = _PACKAGE.parent / "schemas"  # engine/schemas/ of a source checkout


class ResultsError(ValueError):
    """A stamp or a summary breaks the results standard; the message names the place."""


def _git(*args, cwd=_PACKAGE):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    except OSError:
        return None


@lru_cache(maxsize=8)
def _t0_lookup(commit: str, results_root: Path) -> str:
    if commit == "unknown" or commit.endswith("-dirty"):
        return "not run"  # changed files: no stored result speaks for this engine
    verdicts = []
    for test in T0_TESTS:
        found = None
        for folder in sorted((results_root / test).glob("*/"), reverse=True):  # run ids sort by time
            try:
                stamp = json.loads((folder / "stamp.json").read_text(encoding="utf-8"))
                summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            ran_on = str(stamp.get("engine_commit", ""))
            if not ran_on or ran_on == "unknown" or ran_on.endswith("-dirty"):
                continue
            same = _git("diff", "--quiet", ran_on, commit, "--", str(_PACKAGE))
            if same is not None and same.returncode == 0:  # the engine code did not change since that run
                found = summary.get("verdict")
                break
        if found not in ("pass", "fail"):
            return "not run"
        verdicts.append(found)
    return "pass" if all(v == "pass" for v in verdicts) else "fail"


def t0_status(commit: str | None = None, results_root=None) -> str:
    """ "pass", "fail" or "not run": the verdict of the consistency gate T0 for the engine at `commit`
    (default: the current one).

    For each of T0.1 to T0.5 the newest stored run (`results/T0.k/<run-id>/`) is taken whose engine
    code (`engine/cosmicmass/`) is the same as at `commit`, by `git diff`. "pass" if all five passed,
    "fail" if one failed, "not run" if one has no such run, if files are changed ("-dirty"), or
    outside git. So a commit that changes the engine reads "not run" until T0 is run on it again."""
    commit = engine_commit() if commit is None else commit
    if results_root is None:
        top = _git("rev-parse", "--show-toplevel")
        if top is None or top.returncode != 0:
            return "not run"
        results_root = Path(top.stdout.strip()) / "results"
    return _t0_lookup(commit, Path(results_root))


@lru_cache(maxsize=1)
def _validators():
    """The validators of the two forms of each file, or None where the check cannot be made."""
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None
    out = {}
    for name in ("stamp", "summary"):
        path = _SCHEMAS / f"{name}.schema.json"
        if not path.exists():
            return None
        defs = json.loads(path.read_text(encoding="utf-8"))["$defs"]
        for form in ("run", "case"):
            out[name, form] = Draft202012Validator({"$ref": f"#/$defs/{form}_{name}", "$defs": defs})
    return out


def validate_outputs(stamp: dict, summary: dict) -> list[str] | None:
    """Problems of a stamp and a summary against the P4 schemas, each as "file: place: what";
    an empty list if both are valid; None if the check cannot be made here (see the module text)."""
    validators = _validators()
    if validators is None:
        return None
    problems = []
    for name, data in (("stamp", stamp), ("summary", summary)):
        data = json.loads(json.dumps(data))  # as it will be on disk (tuples are lists there)
        form = "case" if "cases" in data else "run"
        for error in sorted(validators[name, form].iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
            place = ".".join(str(part) for part in error.absolute_path) or "(top level)"
            problems.append(f"{name}.json: {place}: {error.message}")
    return problems


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
    stamp = {
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
    if settings.meta.get("populations"):  # E5.4: with numerics.seed, they rebuild the same bodies
        stamp["populations"] = settings.meta["populations"]
    return stamp


def write_results(folder: Path, stamp: dict, summary: dict, rows: list) -> None:
    """Write `stamp.json`, `summary.json` and `timeseries.csv` into a new folder, after checking
    the first two against the P4 schemas (`ResultsError` if one breaks them; nothing is written)."""
    problems = validate_outputs(stamp, summary)
    if problems:
        raise ResultsError("the outputs break the results standard: " + "; ".join(problems))
    folder.mkdir(parents=True, exist_ok=False)
    for name, data in (("stamp.json", stamp), ("summary.json", summary)):
        (folder / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with open(folder / "timeseries.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
