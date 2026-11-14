"""Scaffold a new scenario (task P5, docs/WORK-PLAN.md).

    python tools/new_scenario.py T1.1 "Pure masses: does the Composer part stay silent?"

Creates, and never overwrites:
  scenarios/<ID>/settings.json   a valid L0 starting point (two bodies, 10 steps), to be replaced by the setup
                                 of docs/05-scenarios-and-tests.md
  scenarios/<ID>/run.py          runs the settings with the engine's runner and writes results/<ID>/<run-id>/
  team/notes/<ID>.md             the notebook, from team/notes/_TEMPLATE.md
  a registry row in ARCHITECTURE.md, section 2 (rule D18)

Then: write the pre-registration in the notebook and commit it before any production run (D12);
add one line to the architecture change log (section 11) in your pull request.
Check the scaffold at once with: python scenarios/<ID>/run.py --dry-run
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Z][A-Za-z0-9]*(\.[A-Za-z0-9]+)*$")
REGISTRY_END = "<!-- registry:end -->"

__all__ = ["scaffold", "default_settings", "main", "ScaffoldError"]


class ScaffoldError(ValueError):
    """The scenario cannot be scaffolded; the message says why."""


def default_settings(scenario: str) -> dict:
    """A valid starting point under the reference law L0: a proton and an electron at 1e-10 m,
    at rest, 10 steps. Exploratory (`preregistered: false`) until the notebook is committed."""
    return {
        "scenario": scenario,
        "universe": {"phi_bar_deg": 79.86, "dimension": 2, "units": "SI", "boundary": "open", "background": "none"},
        "law": {"id": "L0"},
        "bodies": [{"preset": "proton", "x": [0.0, 0.0]}, {"preset": "electron", "x": [1e-10, 0.0]}],
        "numerics": {"steps": 10, "softening": 0.0},
        "kind": "finding",
        "preregistered": False,
        "producer": "",
    }


RUN_TEMPLATE = '''"""{scenario}: {title}

Setup and pass criterion: docs/05-scenarios-and-tests.md. Notebook (pre-registration first, D12):
team/notes/{scenario}.md. Settings: scenarios/{scenario}/settings.json.

    python scenarios/{scenario}/run.py [producer]     # writes results/{scenario}/<run-id>/
    python scenarios/{scenario}/run.py --dry-run      # 10 steps, writes nothing
"""

import json
import sys
from pathlib import Path

from cosmicmass.runner import run

HERE = Path(__file__).resolve().parent
PRODUCER = ""  # "@handle" or "agent / model (sponsor @handle)"


def settings(dry_run: bool = False, producer: str = PRODUCER) -> dict:
    data = json.loads((HERE / "settings.json").read_text(encoding="utf-8"))
    data["producer"] = producer
    if dry_run:
        data["numerics"] = {{**data.get("numerics", {{}}), "steps": 10, "t_end": None}}
    return data


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv[1:]
    names = [a for a in sys.argv[1:] if a != "--dry-run"]
    result = run(settings(dry_run, names[0] if names else PRODUCER), out_root=None if dry_run else "results")
    drift = result.summary["conservation"]
    print(f"{scenario}, law {{result.summary['law']}}: {{result.summary['steps']}} steps; "
          f"energy (Re) drift {{drift['energy_re']}}, momentum drift {{drift['momentum']}}")
    print("dry run: nothing written" if dry_run else f"results in {{result.folder}}")
'''


def _notebook(root: Path, scenario: str, title: str) -> str:
    template = (root / "team" / "notes" / "_TEMPLATE.md").read_text(encoding="utf-8")
    text = template.replace("# <ID>: <title>", f"# {scenario}: {title}", 1)
    text = text.replace("<ID>-<short-name>", f"{scenario}-<short-name>")
    text = text.replace("- **Claimed:** YYYY-MM-DD, issue #", f"- **Claimed:** {date.today():%Y-%m-%d}, issue #")
    return text.replace("<ID>", scenario)


def _registry_row(scenario: str, title: str) -> str:
    return f"| - | `scenarios/{scenario}/` | {scenario} | in-progress | {title.replace('|', '/')} |"


def scaffold(scenario: str, title: str, root: Path = ROOT) -> list[Path]:
    """Create the four pieces of a new scenario under `root`; return the paths written."""
    root = Path(root)
    if not ID_PATTERN.match(scenario):
        raise ScaffoldError(f"scenario ID {scenario!r} must look like T1.1, T4.3 or UI2 (letters, digits, dots)")
    if not title.strip():
        raise ScaffoldError("give a title")
    folder = root / "scenarios" / scenario
    notebook = root / "team" / "notes" / f"{scenario}.md"
    architecture = root / "ARCHITECTURE.md"
    for path in (folder, notebook):
        if path.exists():
            raise ScaffoldError(f"{path.relative_to(root).as_posix()} already exists; nothing was written")
    text = architecture.read_text(encoding="utf-8")
    if f"`scenarios/{scenario}/`" in text:
        raise ScaffoldError(f"ARCHITECTURE.md already has a row for scenarios/{scenario}/; nothing was written")
    if REGISTRY_END not in text:
        raise ScaffoldError("ARCHITECTURE.md: the registry end marker was not found; nothing was written")

    folder.mkdir(parents=True)
    (folder / "settings.json").write_text(json.dumps(default_settings(scenario), indent=2) + "\n", encoding="utf-8")
    (folder / "run.py").write_text(RUN_TEMPLATE.format(scenario=scenario, title=title.strip()), encoding="utf-8")
    notebook.write_text(_notebook(root, scenario, title.strip()), encoding="utf-8")
    architecture.write_text(
        text.replace(REGISTRY_END, _registry_row(scenario, title.strip()) + "\n" + REGISTRY_END, 1), encoding="utf-8"
    )
    return [folder / "settings.json", folder / "run.py", notebook, architecture]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new scenario (task P5).")
    parser.add_argument("scenario", help="the scenario ID, for example T1.1")
    parser.add_argument("title", help="a short title, in the language of the cosmic mass")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        written = scaffold(args.scenario, args.title, Path(args.root))
    except ScaffoldError as exc:
        print(f"error: {exc}")
        return 2
    for path in written:
        print(f"wrote {path}")
    print(
        f"next: the pre-registration in team/notes/{args.scenario}.md (commit it first, D12); the setup in "
        f"scenarios/{args.scenario}/settings.json; a line in ARCHITECTURE.md, section 11; then "
        f"python scenarios/{args.scenario}/run.py --dry-run"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
