"""The convergence helper (task E8.2; `team/RESULTS-STANDARD.md`, section 4: "convergence: the same
quantities at `dt/2` and `dt/4`, and at a smaller and a larger particle count, with the relative
changes"; section 5: "change < 1% between `dt/2` and `dt/4`, and between particle counts").

    block = convergence(settings, measure)                         # the step: eta (or dt) / 2, / 4
    block = convergence(settings, measure, counts=(50, 500), resize=my_resize)   # and body counts

`measure(result) -> dict` returns the quantities to compare (numbers) from a `RunResult`. With the
adaptive step (D10) the step is set by `eta`, so "dt/2" means `eta/2`; with a fixed step it is
`dt_initial / 2`. `resize(settings, n)` returns the settings with `n` bodies; it belongs to the
scenario, because only the scenario knows how its population is built.
"""

import copy

from ..runner import run

__all__ = ["convergence", "TOLERANCE"]

TOLERANCE = 0.01  # the default of the results standard, section 5: change below 1%


def _relative(a: float, b: float) -> float | None:
    scale = max(abs(a), abs(b))
    return abs(a - b) / scale if scale else 0.0


def _changes(first: dict, second: dict) -> dict:
    return {k: _relative(first[k], second[k]) for k in first if k in second}


def _with_step(settings: dict, factor: float) -> dict:
    out = copy.deepcopy(settings)
    numerics = out.setdefault("numerics", {})
    if numerics.get("adaptive", True):
        numerics["eta"] = numerics.get("eta", 1e-3) * factor
    else:
        numerics["dt_initial"] = numerics["dt_initial"] * factor
    return out


def convergence(settings: dict, measure, counts=(), resize=None, tolerance: float = TOLERANCE) -> dict:
    """Run `settings` at the step, half and a quarter of it (and at each body count in `counts`),
    measure each run, and return the convergence block of the results standard."""
    runs = {}
    for name, factor in (("step", 1.0), ("step/2", 0.5), ("step/4", 0.25)):
        runs[name] = measure(run(_with_step(settings, factor), out_root=None))
    block = {
        "step": runs,
        "change_step_half_to_quarter": _changes(runs["step/2"], runs["step/4"]),
        "change_step_to_half": _changes(runs["step"], runs["step/2"]),
    }
    largest = list(block["change_step_half_to_quarter"].values())
    if counts:
        if resize is None:
            raise ValueError("other body counts need resize(settings, n), from the scenario")
        by_count = {str(n): measure(run(resize(copy.deepcopy(settings), n), out_root=None)) for n in counts}
        base = runs["step"]
        block["counts"] = by_count
        block["change_with_count"] = {n: _changes(base, values) for n, values in by_count.items()}
        largest += [c for changes in block["change_with_count"].values() for c in changes.values()]
    block["largest_change"] = max((c for c in largest if c is not None), default=0.0)
    block["tolerance"] = tolerance
    block["converged"] = bool(block["largest_change"] < tolerance)
    return block
