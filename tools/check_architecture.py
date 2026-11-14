#!/usr/bin/env python3
"""Check that ARCHITECTURE.md is in step with the code (decision D18).

Checks:
  1. Every code file in engine/, scenarios/, simulator/ and tools/ is covered by a
     row of the module registry (a file row, or the row of a folder containing it).
  2. Rows with status in-progress or implemented point to paths that exist;
     rows with status planned point to paths that do not exist yet.
  3. Every registry node ID (other than "-") appears in at least one Mermaid diagram.
  4. With --base <git ref>: if code files changed since that ref, ARCHITECTURE.md
     changed too.

Usage:
  python tools/check_architecture.py                 # checks 1-3
  python tools/check_architecture.py --base origin/main   # checks 1-4

Exit code 0 when everything passes, 1 otherwise.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCH = ROOT / "ARCHITECTURE.md"
CODE_DIRS = ("engine/", "scenarios/", "simulator/", "tools/")
CODE_EXT = {".py", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".html", ".ipynb", ".c", ".cpp", ".h", ".rs", ".jl", ".go"}
STATUSES = {"planned", "in-progress", "implemented", "deprecated"}
TOO_COARSE = {"engine/", "scenarios/", "simulator/", "tools/", "engine/cosmicmass/"}


def is_code(path: str) -> bool:
    p = path.replace("\\", "/")
    return p.startswith(CODE_DIRS) and Path(p).suffix.lower() in CODE_EXT


def parse_registry(text: str):
    m = re.search(r"<!-- registry:start -->(.*?)<!-- registry:end -->", text, re.S)
    if not m:
        return None, ["registry markers <!-- registry:start/end --> not found"]
    rows, errors = [], []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| Node"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            errors.append(f"registry row has fewer than 5 columns: {line}")
            continue
        node, path_cell, task, status = cells[0], cells[1], cells[2], cells[3]
        pm = re.fullmatch(r"`([^`]+)`", path_cell)
        if not pm:
            errors.append(f"registry path must be in backticks: {line}")
            continue
        path = pm.group(1).replace("\\", "/")
        if status not in STATUSES:
            errors.append(f"{path}: status '{status}' is not one of {sorted(STATUSES)}")
        if path in TOO_COARSE:
            errors.append(f"{path}: a whole top-level folder is too coarse; register files or sub-folders")
        rows.append({"node": node, "path": path, "task": task, "status": status})
    return rows, errors


def mermaid_text(text: str) -> str:
    return "\n".join(re.findall(r"```mermaid\n(.*?)```", text, re.S))


def code_files():
    files = []
    for d in CODE_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.is_file() and "__pycache__" not in f.parts:
                rel = f.relative_to(ROOT).as_posix()
                if is_code(rel):
                    files.append(rel)
    return sorted(files)


def covered(path: str, rows) -> bool:
    if Path(path).name == "__init__.py":
        return True
    for r in rows:
        p = r["path"]
        if path == p or (p.endswith("/") and path.startswith(p)):
            return True
    return False


def changed_files(base: str):
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        out = subprocess.run(["git", "diff", "--name-only", base, "HEAD"], cwd=ROOT, capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip())
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", help="git ref to compare with (pull requests: origin/main)")
    args = ap.parse_args()

    errors = []
    if not ARCH.exists():
        print("FAIL: ARCHITECTURE.md is missing")
        return 1
    text = ARCH.read_text(encoding="utf-8")
    rows, errs = parse_registry(text)
    errors += errs
    rows = rows or []
    diagrams = mermaid_text(text)
    if not diagrams.strip():
        errors.append("ARCHITECTURE.md has no Mermaid diagrams")

    # 1. coverage
    files = code_files()
    for f in files:
        if not covered(f, rows):
            errors.append(f"{f}: code file not in the module registry (ARCHITECTURE.md, section 2)")

    # 2. status matches the disk
    for r in rows:
        exists = (ROOT / r["path"]).exists()
        if r["status"] in ("in-progress", "implemented") and not exists:
            errors.append(f"{r['path']}: status '{r['status']}' but the path does not exist")
        if r["status"] == "planned" and exists:
            errors.append(f"{r['path']}: exists but its status is still 'planned'; update it")

    # 3. every node in a diagram
    for r in rows:
        n = r["node"]
        if n in ("-", ""):
            if not r["path"].startswith("scenarios/"):
                errors.append(f"{r['path']}: needs a diagram node ID (only scenarios may use '-')")
            continue
        if not re.search(rf"(?<![\w/.-]){re.escape(n)}(?![\w-])", diagrams):
            errors.append(f"{r['path']}: node '{n}' does not appear in any Mermaid diagram")

    # 4. D18: code changes come with an architecture update
    if args.base:
        try:
            changed = changed_files(args.base)
        except RuntimeError as exc:
            errors.append(f"could not compare with {args.base}: {exc}")
            changed = []
        code_changed = [c for c in changed if is_code(c)]
        if code_changed and "ARCHITECTURE.md" not in changed:
            errors.append("code changed but ARCHITECTURE.md did not (rule D18): " + ", ".join(code_changed[:10]))

    print(
        f"Architecture check: {len(rows)} registry rows, {len(files)} code files, "
        f"{len(re.findall(r'```mermaid', text))} diagrams"
    )
    if errors:
        for e in errors:
            print("FAIL:", e)
        print(f"{len(errors)} problem(s). See ARCHITECTURE.md, section 12.")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
