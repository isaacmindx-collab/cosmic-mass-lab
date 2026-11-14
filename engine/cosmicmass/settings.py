"""Load and validate the settings of a run (task E5.3, minimal version of the MVP).

A settings file is JSON in the vocabulary of `stamp.json` (`team/RESULTS-STANDARD.md`,
section 2): `scenario`, `universe`, `law`, `bodies`, `numerics`. Every error names
the bad field. This minimal loader covers what the MVP needs; `Universe` (E5.2),
populations (E5.4) and the JSON schemas (P4) will extend it.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .environment import K_B, Environment, HeatBath, Inflow
from .frame import DEFAULT_PHI_BAR_DEG, Frame
from .laws import Law, LawSpec, make_law
from .matter import PRESETS, CosmicMass
from .state import State

__all__ = ["Settings", "SettingsError", "load_settings", "make_inflow", "make_heat_bath"]

# decision D10: velocity Verlet, adaptive step, softening 1e-3 of the smallest separation
_NUMERICS = {
    "integrator": None,  # resolved below: "boris" with a background B_g or b, otherwise "verlet" (D10)
    "adaptive": True,
    "dt_initial": None,
    "softening": None,
    "softening_fraction": 1e-3,
    "eta": 1e-3,
    "dt_min": 0.0,
    "dt_max": None,
    "speed_reference": "neighbour",  # D29 (was "absolute" under D21)
    "steps": None,
    "t_end": None,
    "record_every": None,
    "seed": 0,
}
_UNIVERSE = {
    "phi_bar_deg": None,
    "dimension": 2,
    "units": "SI",
    "boundary": "open",
    "background": "none",
    "box": None,
    "inflow": None,
    "heat_bath": None,
}
_INFLOW = {"preset", "name", "m", "q", "rate", "velocity", "face"}
_TOP = {"scenario", "universe", "law", "bodies", "numerics", "kind", "preregistered", "producer"}
_BODY = {"preset", "name", "m", "q", "x", "v", "fixed"}


class SettingsError(ValueError):
    """A settings file is invalid; the message names the bad field."""


def _known(block: dict, allowed, where: str) -> None:
    if not isinstance(block, dict):
        raise SettingsError(f"'{where}' must be an object")
    unknown = sorted(set(block) - set(allowed))
    if unknown:
        raise SettingsError(f"unknown field(s) {unknown} in '{where}'; known: {sorted(allowed)}")


@dataclass
class Settings:
    scenario: str
    frame: Frame
    universe: dict
    law_spec: LawSpec
    state: State
    bodies: list
    numerics: dict
    meta: dict = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        return self.universe["dimension"]

    def make_law(self) -> Law:
        return make_law(self.law_spec)


def _body(entry: dict, index: int, dimension: int, units: str):
    where = f"bodies[{index}]"
    _known(entry, _BODY, where)
    if "preset" in entry:
        if units != "SI":
            raise SettingsError(f"'{where}.preset': the presets are SI values; give 'm' and 'q' in scaled units")
        if entry["preset"] not in PRESETS:
            raise SettingsError(f"'{where}.preset': unknown preset {entry['preset']!r}; known: {sorted(PRESETS)}")
        body = PRESETS[entry["preset"]]
        if "q" in entry:
            body = body.with_charge(float(entry["q"]))
        if "m" in entry:
            raise SettingsError(f"'{where}': give either 'preset' or 'm', not both")
    elif "m" in entry and "q" in entry:
        body = CosmicMass(float(entry["m"]), float(entry["q"]), str(entry.get("name", "")))
    else:
        raise SettingsError(f"'{where}': give a 'preset', or both 'm' and 'q'")
    vectors = []
    for key in ("x", "v"):
        value = entry.get(key, [0.0] * dimension if key == "v" else None)
        if not isinstance(value, list) or len(value) != dimension:
            raise SettingsError(f"'{where}.{key}' must be a list of {dimension} numbers")
        vectors.append([float(c) for c in value])
    return body, vectors[0], vectors[1], bool(entry.get("fixed", False))


def _inflow(universe: dict) -> dict:
    """Setting U7, normalised: `{"name", "m", "q", "rate", "velocity", "face": {"axis", "side"}}`."""
    entry, where = universe["inflow"], "universe.inflow"
    _known(entry, _INFLOW, where)
    if universe["boundary"] == "open":
        raise SettingsError(f"'{where}': the inflow enters a box; set 'universe.boundary' and 'universe.box'")
    if "preset" in entry:
        if universe["units"] != "SI" or "m" in entry or "q" in entry:
            raise SettingsError(f"'{where}': give a 'preset' (SI only), or both 'm' and 'q'")
        body = PRESETS.get(entry["preset"])
        if body is None:
            raise SettingsError(f"'{where}.preset': unknown preset {entry['preset']!r}; known: {sorted(PRESETS)}")
        m, q, name = body.m, body.q, entry.get("name", body.name)
    elif "m" in entry and "q" in entry:
        m, q, name = float(entry["m"]), float(entry["q"]), str(entry.get("name", ""))
    else:
        raise SettingsError(f"'{where}': give a 'preset', or both 'm' and 'q'")
    face = entry.get("face")
    _known(face if isinstance(face, dict) else 0, ("axis", "side"), f"{where}.face")
    out = {
        "name": name,
        "m": m,
        "q": q,
        "rate": entry.get("rate"),
        "velocity": entry.get("velocity"),
        "face": {"axis": face.get("axis"), "side": face.get("side")},
    }
    try:
        make_inflow(out, universe["box"])
    except (ValueError, TypeError) as exc:
        raise SettingsError(f"'{where}': {exc}") from None
    out["rate"], out["velocity"] = float(out["rate"]), [float(c) for c in out["velocity"]]
    return out


def _heat_bath(entry, units: str) -> dict:
    _known(entry, ("temperature", "collision_rate"), "universe.heat_bath")
    try:
        HeatBath(entry.get("temperature"), entry.get("collision_rate"), K_B[units])
    except (ValueError, TypeError):
        raise SettingsError(
            "'universe.heat_bath' needs a positive 'temperature' and a positive 'collision_rate'"
        ) from None
    return {"temperature": float(entry["temperature"]), "collision_rate": float(entry["collision_rate"])}


def make_inflow(spec: dict, box: dict, t0: float = 0.0) -> Inflow:
    """The `Inflow` of a normalised inflow block and the box, counting from `t0`."""
    return Inflow(
        spec["m"],
        spec["q"],
        spec["rate"],
        spec["velocity"],
        spec["face"]["axis"],
        spec["face"]["side"],
        box["lower"],
        box["upper"],
        spec.get("name", ""),
        t0=t0,
    )


def make_heat_bath(spec: dict, units: str) -> HeatBath:
    return HeatBath(spec["temperature"], spec["collision_rate"], K_B[units])


def load_settings(source) -> Settings:
    """Load settings from a path to a JSON file, or from a dictionary."""
    data = source if isinstance(source, dict) else json.loads(Path(source).read_text(encoding="utf-8"))
    _known(data, _TOP, "settings")
    for required in ("scenario", "bodies"):
        if required not in data:
            raise SettingsError(f"missing field '{required}'")

    _known(data.get("universe", {}), _UNIVERSE, "universe")
    universe = {**_UNIVERSE, **data.get("universe", {})}
    if universe["units"] not in ("SI", "scaled"):
        raise SettingsError("'universe.units' must be 'SI' or 'scaled'")
    if universe["dimension"] not in (2, 3):
        raise SettingsError("'universe.dimension' must be 2 or 3")
    if universe["phi_bar_deg"] is None:  # 79.86 degrees in SI, 90 degrees in scaled units
        universe["phi_bar_deg"] = DEFAULT_PHI_BAR_DEG if universe["units"] == "SI" else 90.0
    try:
        make_frame = Frame.si if universe["units"] == "SI" else Frame.scaled
        frame = make_frame(universe["phi_bar_deg"])
    except (ValueError, TypeError) as exc:
        raise SettingsError(f"'universe.phi_bar_deg': {exc}") from None

    background = universe["background"]
    if background != "none":  # uniform fields (setting U5): any of g, e, B_g, b
        _known(background, ("g", "e", "B_g", "b"), "universe.background")
        for key, value in background.items():
            second_2d = key in ("B_g", "b") and universe["dimension"] == 2
            ok = (
                isinstance(value, (int, float))
                if second_2d
                else (isinstance(value, list) and len(value) == universe["dimension"])
            )
            if not ok:
                shape = "a number" if second_2d else f"a list of {universe['dimension']} numbers"
                raise SettingsError(f"'universe.background.{key}' must be {shape}")
    if universe["boundary"] not in Environment.BOUNDARIES:
        raise SettingsError(f"'universe.boundary' must be one of {list(Environment.BOUNDARIES)}")
    if universe["boundary"] != "open":  # the box: its lower and upper corners
        box = universe["box"]
        _known(box if box is not None else 0, ("lower", "upper"), "universe.box")
        try:
            Environment(universe["boundary"], box.get("lower"), box.get("upper"))
            assert len(box["lower"]) == universe["dimension"]
        except (ValueError, TypeError, AssertionError):
            raise SettingsError(
                f"'universe.box' needs 'lower' and 'upper', lists of {universe['dimension']} numbers with lower < upper"
            ) from None
    if universe["inflow"] is not None:
        universe["inflow"] = _inflow(universe)
    if universe["heat_bath"] is not None:
        universe["heat_bath"] = _heat_bath(universe["heat_bath"], universe["units"])

    try:
        law_spec = LawSpec.from_dict(data.get("law", {"id": "L0"}))
    except (ValueError, TypeError) as exc:
        raise SettingsError(f"'law': {exc}") from None

    if not isinstance(data["bodies"], list) or not data["bodies"]:
        raise SettingsError("'bodies' must be a non-empty list")
    parsed = [_body(b, i, universe["dimension"], universe["units"]) for i, b in enumerate(data["bodies"])]
    bodies = [p[0] for p in parsed]
    state = State.from_bodies(bodies, [p[1] for p in parsed], [p[2] for p in parsed], [p[3] for p in parsed])

    _known(data.get("numerics", {}), _NUMERICS, "numerics")
    numerics = {**_NUMERICS, **data.get("numerics", {})}
    if numerics["integrator"] is None:  # D10: velocity Verlet, Boris with a second field B_cal
        magnetic = background != "none" and any(
            np.any(np.asarray(background.get(key, 0.0)) != 0) for key in ("B_g", "b")
        )
        numerics["integrator"] = "boris" if magnetic else "verlet"
    if numerics["integrator"] not in ("verlet", "boris"):
        raise SettingsError("'numerics.integrator' must be 'verlet' or 'boris'")
    meta = {
        "kind": data.get("kind", "finding"),
        "preregistered": bool(data.get("preregistered", False)),
        "producer": data.get("producer", ""),
    }
    if meta["kind"] not in ("mathematics", "measurement-check", "finding"):
        raise SettingsError("'kind' must be 'mathematics', 'measurement-check' or 'finding'")
    return Settings(str(data["scenario"]), frame, universe, law_spec, state, bodies, numerics, meta)
