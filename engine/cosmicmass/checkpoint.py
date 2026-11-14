"""Checkpoints of a run (task E7.1): save everything the time loop holds, and take it up again.

A checkpoint is one `.npz` file: the arrays of the run (the columns of the state, the
remembered acceleration and fields of the step context, the momentum given to the walls,
the temperatures) and one JSON text with the rest (the step, the time, the rows of the
time series, the counters of the environment, the state of the random generator).
It is read with `allow_pickle=False`: a checkpoint is data, it cannot run code.

The aim is the done-when of E7.1: "a run interrupted and resumed gives the same result".
So the checkpoint holds every value the loop would otherwise carry in memory, bit for bit,
and it carries a key (`run_key`) made of the stamp (the settings and the engine commit) and
the initial state: a checkpoint is refused by a run with other settings, other bodies or
another engine.

The file is written beside its final name and then moved over it, so a run killed while
writing leaves the previous checkpoint whole.
"""

import hashlib
import json
import os
from dataclasses import fields as dataclass_fields
from pathlib import Path

import numpy as np

from .fields.sample import FieldSample
from .state import State

__all__ = ["CheckpointError", "FORMAT", "run_key", "save", "load", "pack_state", "unpack_state"]

FORMAT = 1  # raised when the content of a checkpoint changes
_SAMPLE = ("g", "e", "B_g", "b")
# keys of `numerics` that do not change what the run computes: a run may be resumed with others
_FREE_NUMERICS = ("checkpoint_every",)


class CheckpointError(ValueError):
    """A checkpoint is missing, unreadable, or belongs to another run."""


def _plain(value):
    """NumPy scalars and arrays as plain Python values, for the JSON part."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"cannot store {type(value).__name__} in a checkpoint")


def run_key(stamp: dict, state: State | None = None) -> str:
    """The identity of a run for resuming: its stamp without the run id and the T0 status (they
    belong to the moment of writing) and without the numerics that do not change the result;
    and its initial state, which the stamp does not hold (it names the bodies, not where they are)."""
    kept = {k: v for k, v in stamp.items() if k not in ("run_id", "t0_status", "resumed_at_steps")}
    kept["numerics"] = {k: v for k, v in stamp["numerics"].items() if k not in _FREE_NUMERICS}
    digest = hashlib.sha256(json.dumps(kept, sort_keys=True, default=_plain).encode("utf-8"))
    if state is not None:
        arrays, plain = pack_state(state)
        digest.update(json.dumps(plain, sort_keys=True, default=_plain).encode("utf-8"))
        for name in sorted(arrays):
            digest.update(name.encode("utf-8") + str(arrays[name].shape).encode("utf-8"))
            digest.update(np.ascontiguousarray(arrays[name]).tobytes())
    return digest.hexdigest()


def pack_state(state: State, prefix: str = "state.") -> tuple[dict, dict]:
    """The columns of a state as arrays, and its other fields (the time) as plain values.
    Every array field is taken by name, so a column added to `State` later is saved too."""
    arrays, plain = {}, {}
    for item in dataclass_fields(state):
        value = getattr(state, item.name)
        if isinstance(value, np.ndarray):
            arrays[prefix + item.name] = value
        else:
            plain[item.name] = value
    return arrays, plain


def unpack_state(arrays: dict, plain: dict, prefix: str = "state.") -> State:
    columns = {name[len(prefix) :]: np.array(value) for name, value in arrays.items() if name.startswith(prefix)}
    known = {item.name for item in dataclass_fields(State)}
    unknown = sorted((set(columns) | set(plain)) - known)
    if unknown:
        raise CheckpointError(f"the checkpoint has state columns this engine does not know: {unknown}")
    return State(**columns, **plain)


def _pack_sample(sample: FieldSample, prefix: str) -> dict:
    arrays = {prefix + name: getattr(sample, name) for name in _SAMPLE}
    if sample.screened is not None:
        arrays.update(_pack_sample(sample.screened, prefix + "screened."))
    return arrays


def _unpack_sample(arrays: dict, prefix: str) -> FieldSample:
    screened = _unpack_sample(arrays, prefix + "screened.") if prefix + "screened.g" in arrays else None
    return FieldSample(**{name: np.array(arrays[prefix + name]) for name in _SAMPLE}, screened=screened)


def save(path, key: str, state: State, cache, arrays: dict, book: dict) -> Path:
    """Write a checkpoint. `cache` is the step context's `(state, a, fields, inertia)` or None;
    `arrays` are the other arrays of the loop, `book` everything else (JSON values)."""
    path = Path(path)
    state_arrays, state_plain = pack_state(state)
    content = {**state_arrays, **{f"loop.{name}": np.asarray(value) for name, value in arrays.items()}}
    remembered = cache is not None and cache[0] is state
    if remembered:
        content["cache.a"], content["cache.inertia"] = cache[1], cache[3]
        content.update(_pack_sample(cache[2], "cache.fields."))
    meta = {"format": FORMAT, "key": key, "state": state_plain, "remembered": remembered, "book": book}
    content["meta"] = np.array(json.dumps(meta, default=_plain))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".writing")
    with open(temporary, "wb") as handle:
        np.savez(handle, **content)
    os.replace(temporary, path)  # a run killed while writing leaves the previous checkpoint whole
    return path


def load(path, key: str) -> tuple:
    """Read a checkpoint of the run `key`: `(state, cache, arrays, book)`, where `cache` is
    `(a, fields, inertia)` for the step context, or None."""
    path = Path(path)
    if not path.exists():
        raise CheckpointError(f"no checkpoint at {path}")
    try:
        with np.load(path, allow_pickle=False) as data:
            content = {name: data[name] for name in data.files}
        meta = json.loads(str(content.pop("meta")))
    except (OSError, ValueError, KeyError) as exc:
        raise CheckpointError(f"the checkpoint {path} cannot be read ({exc})") from None
    if meta.get("format") != FORMAT:
        raise CheckpointError(f"the checkpoint {path} has format {meta.get('format')}, this engine reads {FORMAT}")
    if meta.get("key") != key:
        raise CheckpointError(
            f"the checkpoint {path} belongs to another run: other settings or another engine commit. "
            "Run without resuming, or with the settings and the commit that wrote it."
        )
    state = unpack_state(content, meta["state"])
    cache = None
    if meta["remembered"]:
        cache = (np.array(content["cache.a"]), _unpack_sample(content, "cache.fields."), content["cache.inertia"])
    arrays = {name[len("loop.") :]: np.array(value) for name, value in content.items() if name.startswith("loop.")}
    return state, cache, arrays, meta["book"]
