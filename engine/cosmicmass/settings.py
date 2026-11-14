"""Load and validate the settings of a run (task E5.3).

A settings file is JSON in the vocabulary of `stamp.json` (`team/RESULTS-STANDARD.md`,
section 2): `scenario`, `universe`, `law`, `bodies`, `populations`, `numerics`. Every error
names the bad field. The `universe` block is validated by `Universe` (E5.2, `universe.py`),
the `law` block by `LawSpec`, the populations by `populations.py`; the numerics take the
defaults of decision D10.

The law: an object (`{"id": "L1a", "lambda": 0.5, ...}`), or one of two names:
`"reference"` (L0) and `"exploratory"`, the default exploratory law of
`docs/05-scenarios-and-tests.md` (L1a, sign +, lambda 1, radial, all terms, L6 off, inertia
`Re(mu)`, `1/r^2`). A settings file with no `law` runs the reference law L0 (a labelled
choice: question 29 of `team/QUESTIONS.md`).
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .constants import SI, scaled
from .frame import Frame
from .laws import Law, LawSpec, make_law
from .matter import PRESETS, CosmicMass
from .populations import POPULATION_KEYS, SHAPES, generate
from .state import State
from .universe import Universe, UniverseError, make_heat_bath, make_inflow

__all__ = [
    "Settings",
    "SettingsError",
    "load_settings",
    "make_inflow",
    "make_heat_bath",
    "NAMED_LAWS",
    "DEFAULT_EXPLORATORY_LAW",
]

# docs/05-scenarios-and-tests.md, "Default exploratory law" (a hypothesis, decision D1)
DEFAULT_EXPLORATORY_LAW = {
    "id": "L1a",
    "sign": "+",
    "lambda": 1.0,
    "direction": "radial",
    "terms": "all",
    "B_cal": "off",
    "inertia": "Re",
    "range": "1/r^2",
}
NAMED_LAWS = {"reference": {"id": "L0"}, "exploratory": DEFAULT_EXPLORATORY_LAW}

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
_TOP = {"scenario", "universe", "law", "bodies", "populations", "numerics", "kind", "preregistered", "producer"}
_BODY = {"preset", "name", "m", "q", "x", "v", "fixed", "xc", "vc", "spin", "radius"}


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
    world: Universe | None = None  # E5.2: the universe as an object; `universe` is its dictionary form

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
    extra = {}  # the optional columns of D37, only those given
    for key in ("xc", "vc"):
        if key in entry:
            if not isinstance(entry[key], list) or len(entry[key]) != dimension:
                raise SettingsError(f"'{where}.{key}' must be a list of {dimension} numbers")
            extra[key] = [float(c) for c in entry[key]]
    if "spin" in entry:
        spin = entry["spin"]
        ok = isinstance(spin, (int, float)) if dimension == 2 else (isinstance(spin, list) and len(spin) == 3)
        if not ok or isinstance(spin, bool):
            raise SettingsError(f"'{where}.spin' must be " + ("a number" if dimension == 2 else "a list of 3 numbers"))
        extra["spin"] = float(spin) if dimension == 2 else [float(c) for c in spin]
    if "radius" in entry:
        radius = entry["radius"]
        if isinstance(radius, bool) or not isinstance(radius, (int, float)) or radius < 0:
            raise SettingsError(f"'{where}.radius' must be a number, not negative")
        extra["radius"] = float(radius)
    return body, vectors[0], vectors[1], bool(entry.get("fixed", False)), extra


def _population(entry, index: int, universe: dict) -> tuple:
    """One entry of `populations` (E5.4), checked; returns the real particle and the spec."""
    where, d = f"populations[{index}]", universe["dimension"]
    _known(entry, POPULATION_KEYS, where)
    if "preset" in entry:
        if universe["units"] != "SI" or "m" in entry or "q" in entry:
            raise SettingsError(f"'{where}': give a 'preset' (SI only), or both 'm' and 'q'")
        if entry["preset"] not in PRESETS:
            raise SettingsError(f"'{where}.preset': unknown preset {entry['preset']!r}; known: {sorted(PRESETS)}")
        body = PRESETS[entry["preset"]]
    elif "m" in entry and "q" in entry:
        body = CosmicMass(float(entry["m"]), float(entry["q"]), str(entry.get("name", "")))
    else:
        raise SettingsError(f"'{where}': give a 'preset', or both 'm' and 'q'")
    spec = dict(entry)
    n = spec.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise SettingsError(f"'{where}.n' must be a positive whole number")
    shape = spec.get("shape", "box")
    spec["shape"] = shape
    if shape not in SHAPES:
        raise SettingsError(f"'{where}.shape' must be one of {list(SHAPES)}")

    def vector(key, default=None):
        value = spec.get(key, default)
        if not isinstance(value, list) or len(value) != d:
            raise SettingsError(f"'{where}.{key}' must be a list of {d} numbers")
        return [float(c) for c in value]

    if shape == "box":
        box = universe.get("box") or {}
        spec["lower"], spec["upper"] = vector("lower", box.get("lower")), vector("upper", box.get("upper"))
        if not all(lo < hi for lo, hi in zip(spec["lower"], spec["upper"])):
            raise SettingsError(f"'{where}': lower must be below upper on every axis")
    else:
        spec["centre"] = vector("centre", [0.0] * d)
        radius, width = spec.get("radius"), spec.get("width", 0.0)
        if not isinstance(radius, (int, float)) or not isinstance(width, (int, float)) or not 0 <= width < 2 * radius:
            raise SettingsError(f"'{where}': give a 'radius' > 0 and a 'width' between 0 and twice the radius")
    spec["bulk"] = vector("bulk", [0.0] * d)
    for key in ("temperature", "weight"):
        value = spec.get(key, 0.0 if key == "temperature" else 1.0)
        if not isinstance(value, (int, float)) or value < 0 or (key == "weight" and value == 0):
            raise SettingsError(
                f"'{where}.{key}' must be a number, not negative" + (", not zero" if key == "weight" else "")
            )
    if "keplerian" in spec:
        kepler = spec["keplerian"]
        _known(kepler if isinstance(kepler, dict) else 0, ("mass", "centre"), f"{where}.keplerian")
        if not isinstance(kepler.get("mass"), (int, float)) or kepler["mass"] <= 0:
            raise SettingsError(f"'{where}.keplerian.mass' must be a positive number")
    return body, spec


def load_settings(source) -> Settings:
    """Load settings from a path to a JSON file, or from a dictionary."""
    data = source if isinstance(source, dict) else json.loads(Path(source).read_text(encoding="utf-8"))
    _known(data, _TOP, "settings")
    for required in ("scenario",):  # bodies, populations or both: checked below
        if required not in data:
            raise SettingsError(f"missing field '{required}'")

    try:  # E5.2: the universe validates its own block (U1 to U7) and refuses invalid combinations
        world = Universe.from_dict(data.get("universe"))
    except UniverseError as exc:
        raise SettingsError(str(exc)) from None
    universe, frame, background = world.to_dict(), world.frame, world.background

    law = data.get("law", "reference")  # no law given: the reference law L0
    if isinstance(law, str):
        if law not in NAMED_LAWS:
            raise SettingsError(f"'law': unknown name {law!r}; known: {sorted(NAMED_LAWS)}, or an object with 'id'")
        law = NAMED_LAWS[law]
    try:
        law_spec = LawSpec.from_dict(law)
    except (ValueError, TypeError) as exc:
        raise SettingsError(f"'law': {exc}") from None

    _known(data.get("numerics", {}), _NUMERICS, "numerics")
    numerics = {**_NUMERICS, **data.get("numerics", {})}

    listed = data.get("bodies", [])
    populations = data.get("populations", [])
    if not isinstance(listed, list) or not isinstance(populations, list):
        raise SettingsError("'bodies' and 'populations' must be lists")
    if not (listed or populations or world.sources):
        raise SettingsError("give a non-empty list of 'bodies', or 'populations', or both")
    parsed = [_body(b, i, universe["dimension"], universe["units"]) for i, b in enumerate(listed)]
    for source in world.sources:  # U6: the pinned cosmic masses of the universe, after the listed bodies
        body = CosmicMass(source["m"], source["q"], source["name"])
        parsed.append((body, source["x"], [0.0] * universe["dimension"], True, {}))
    bodies = [p[0] for p in parsed]
    x = [p[1] for p in parsed]
    v = [p[2] for p in parsed]
    fixed = [p[3] for p in parsed]
    if populations:  # E5.4: seeded populations, after the listed bodies, in the order given
        rng = np.random.default_rng((int(numerics["seed"]), 1))  # a stream of its own (the runner's is (seed))
        constants = SI if universe["units"] == "SI" else scaled()
        for k, entry in enumerate(populations):
            body, spec = _population(entry, k, universe)
            made = generate(spec, universe["dimension"], constants, rng, (body.m, body.q))
            weighted = CosmicMass(float(made["m"][0]), float(made["q"][0]), body.name)
            bodies += [weighted] * spec["n"]
            x += [list(r) for r in made["x"]]
            v += [list(r) for r in made["v"]]
            fixed += [False] * spec["n"]
        # Super-particles move with the real particle's thermal speeds but carry `weight` times its mass, so
        # every temperature computed from the bodies' own masses (E8 diagnostics, the E6b heat bath) is `weight`
        # times too high. Until the bodies carry their weight (a State column, a maintainer's decision), a heat
        # bath with weighted bodies is refused, and the summary labels the temperature (review of #66).
        if universe["heat_bath"] is not None and any(float(p.get("weight", 1.0)) != 1.0 for p in populations):
            raise SettingsError(
                "'universe.heat_bath' cannot be used with populations of 'weight' other than 1: the bath would "
                "drive super-particles to the temperature of their whole mass, not of the real particles"
            )
    state = State.from_bodies(bodies, x, v, fixed)
    for i, entry in enumerate(parsed):  # the optional columns of D37, for the listed bodies that give them
        for key, value in entry[4].items():
            getattr(state, key)[i] = value
    if numerics["integrator"] is None:  # D10: velocity Verlet, Boris with a second field B_cal
        magnetic = background != "none" and any(
            np.any(np.asarray(background.get(key, 0.0)) != 0) for key in ("B_g", "b")
        )
        magnetic = magnetic or universe["moving_fields"]  # E2.2: the bodies make a second field too
        # the Boris push reads only L0's v x B_cal: with L6 on (law.B_cal), velocity Verlet
        numerics["integrator"] = "boris" if magnetic and law_spec.moving == "off" else "verlet"
    if numerics["integrator"] not in ("verlet", "boris"):
        raise SettingsError("'numerics.integrator' must be 'verlet' or 'boris'")
    if numerics["integrator"] == "boris" and law_spec.moving != "off":
        raise SettingsError("'numerics.integrator': 'boris' reads only L0's v x B_cal; with law.B_cal on, use 'verlet'")
    meta = {
        "kind": data.get("kind", "finding"),
        "preregistered": bool(data.get("preregistered", False)),
        "producer": data.get("producer", ""),
    }
    if populations:  # as given: with numerics.seed they rebuild the same bodies (E5.4)
        meta["populations"] = populations
    if meta["kind"] not in ("mathematics", "measurement-check", "finding"):
        raise SettingsError("'kind' must be 'mathematics', 'measurement-check' or 'finding'")
    return Settings(str(data["scenario"]), frame, universe, law_spec, state, bodies, numerics, meta, world)
