"""Validate `stamp.json` and `summary.json` against the P4 schemas (team/RESULTS-STANDARD.md).

    python tools/validate_results.py                 # every run folder under results/
    python tools/validate_results.py results/T9.2    # one scenario, or one run folder

Exit code 0 if every file is valid, 1 otherwise. Each problem is printed on one line:
the file, the place in it (for example `cases.a.law.sign`) and what is wrong.
The schemas are `engine/schemas/stamp.schema.json` and `engine/schemas/summary.schema.json`.
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "engine" / "schemas"
FILES = {"stamp.json": "stamp", "summary.json": "summary"}

__all__ = ["load_schema", "validate", "validate_folder", "run_folders", "main"]


def load_schema(name: str) -> dict:
    """`name` is "stamp" or "summary"."""
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def _form(name: str, data) -> str:
    """The form of the file: a test with several cases, or one run. Choosing it first gives
    messages about the form the file claims to be, instead of a bare "not valid under oneOf"."""
    if isinstance(data, dict) and "cases" in data:
        return "case_stamp" if name == "stamp" else "case_summary"
    return "run_stamp" if name == "stamp" else "run_summary"


def _place(error) -> str:
    return ".".join(str(part) for part in error.absolute_path) or "(top level)"


def validate(data, name: str) -> list[str]:
    """Problems of one stamp or summary (`name` is "stamp" or "summary"); an empty list if valid."""
    schema = load_schema(name)
    form = _form(name, data)
    validator = Draft202012Validator({"$ref": f"#/$defs/{form}", "$defs": schema["$defs"]})
    problems = sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path])
    return [f"{_place(e)}: {e.message}" for e in problems]


def validate_folder(folder: Path) -> list[str]:
    """Problems of the two files of one run folder, each prefixed with the file's path."""
    out = []
    for filename, name in FILES.items():
        path = Path(folder) / filename
        if not path.exists():
            out.append(f"{path}: missing")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            out.append(f"{path}: not valid JSON ({exc})")
            continue
        out.extend(f"{path}: {problem}" for problem in validate(data, name))
    return out


def run_folders(root: Path) -> list[Path]:
    """Every folder under `root` (or `root` itself) that holds a stamp.json."""
    root = Path(root)
    return sorted({p.parent for p in root.rglob("stamp.json")})


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    roots = [Path(a) for a in args] or [ROOT / "results"]
    folders = [f for r in roots for f in run_folders(r)]
    if not folders:
        print("no run folder found")
        return 1
    problems = [p for f in folders for p in validate_folder(f)]
    for problem in problems:
        print(problem)
    print(f"{len(folders)} run folder(s): " + ("all valid" if not problems else f"{len(problems)} problem(s)"))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
