"""The universe of a run: the settings U1 to U8 of `docs/05-scenarios-and-tests.md` (task E5.2).

A `Universe` holds what a run's space is, apart from the bodies that move in it:

| Setting | Where it is |
|---|---|
| U1 frame angle | `phi_bar_deg` (default: 79.86 degrees in SI, 90 degrees in scaled units); `angle_sweep()` |
| U2 dimension | `dimension`: 2 (motion in a plane with the `1/r^2` field, decision D21) or 3 |
| U3 units | `units`: "SI" or "scaled"; `in_units()` gives the other for a side-by-side run |
| U4 boundary | `boundary` and `box` (the boundaries of `Environment.BOUNDARIES`) |
| U5 background fields | `background`: "none", or uniform `g`, `e`, `B_g`, `b` |
| U6 fixed sources | `sources`: pinned cosmic masses with their places |
| U7 inflow | `inflow`: rate, cosmic mass and velocity of a stream entering through one face |
| U8 population state | the `populations` of the settings (`populations.py`); `check_population` here checks one against the universe |

`Universe.from_dict` validates a `universe` block and refuses invalid combinations; every error
names the bad field. `to_dict()` gives the block back with every default filled in: it is what
`Settings.universe` holds and what the stamp is built from.
"""

from dataclasses import dataclass, field, replace

from .constants import SI, Constants, scaled
from .environment import K_B, Environment, HeatBath, Inflow
from .frame import DEFAULT_PHI_BAR_DEG, Frame
from .matter import PRESETS

__all__ = ["Universe", "UniverseError", "make_inflow", "make_heat_bath", "UNITS", "BACKGROUND_FIELDS"]

UNITS = ("SI", "scaled")
BACKGROUND_FIELDS = ("g", "e", "B_g", "b")
_KEYS = (
    "phi_bar_deg",
    "dimension",
    "units",
    "boundary",
    "background",
    "box",
    "sources",
    "inflow",
    "heat_bath",
    "moving_fields",
)
_INFLOW = {"preset", "name", "m", "q", "rate", "velocity", "face"}
_SOURCE = {"preset", "name", "m", "q", "x"}


class UniverseError(ValueError):
    """A `universe` block is invalid; the message names the bad field."""


def _known(block, allowed, where: str) -> None:
    if not isinstance(block, dict):
        raise UniverseError(f"'{where}' must be an object")
    unknown = sorted(set(block) - set(allowed))
    if unknown:
        raise UniverseError(f"unknown field(s) {unknown} in '{where}'; known: {sorted(allowed)}")


def _cosmic_mass(entry: dict, units: str, where: str) -> tuple:
    """`(name, m, q)` of an entry that gives a `preset` (SI only), or both `m` and `q`."""
    if "preset" in entry:
        if units != "SI" or "m" in entry or "q" in entry:
            raise UniverseError(f"'{where}': give a 'preset' (SI only), or both 'm' and 'q'")
        body = PRESETS.get(entry["preset"])
        if body is None:
            raise UniverseError(f"'{where}.preset': unknown preset {entry['preset']!r}; known: {sorted(PRESETS)}")
        return entry.get("name", body.name), body.m, body.q
    if "m" in entry and "q" in entry:
        return str(entry.get("name", "")), float(entry["m"]), float(entry["q"])
    raise UniverseError(f"'{where}': give a 'preset', or both 'm' and 'q'")


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


@dataclass(frozen=True)
class Universe:
    """The settings U1 to U7 of a run, validated (see the module text). Build it with `from_dict`."""

    phi_bar_deg: float
    dimension: int = 2
    units: str = "SI"
    boundary: str = "open"
    background: dict | str = "none"
    box: dict | None = None
    sources: tuple = ()  # U6: {"name", "m", "q", "x"} for each pinned cosmic mass
    inflow: dict | None = None  # U7, normalised: {"name", "m", "q", "rate", "velocity", "face": {"axis", "side"}}
    heat_bath: dict | None = None  # {"temperature", "collision_rate"}
    moving_fields: bool = False  # E2.2 (D41): the second field of moving bodies
    frame: Frame = field(default=None, compare=False, repr=False)

    # ------------------------------------------------------------------ building
    @classmethod
    def from_dict(cls, block: dict | None = None) -> "Universe":
        """A universe from the `universe` block of a settings file (None or {}: every default)."""
        block = {} if block is None else block
        _known(block, _KEYS, "universe")
        units = block.get("units", "SI")
        if units not in UNITS:
            raise UniverseError("'universe.units' must be 'SI' or 'scaled'")
        dimension = block.get("dimension", 2)
        if dimension not in (2, 3) or isinstance(dimension, bool):
            raise UniverseError("'universe.dimension' must be 2 or 3")
        phi = block.get("phi_bar_deg")
        if phi is None:  # 79.86 degrees in SI, 90 degrees in scaled units
            phi = DEFAULT_PHI_BAR_DEG if units == "SI" else 90.0
        try:
            frame = (Frame.si if units == "SI" else Frame.scaled)(phi)
        except (ValueError, TypeError) as exc:
            raise UniverseError(f"'universe.phi_bar_deg': {exc}") from None

        background = block.get("background", "none")
        if background != "none":  # uniform fields (U5): any of g, e, B_g, b
            _known(background, BACKGROUND_FIELDS, "universe.background")
            for key, value in background.items():
                second_2d = key in ("B_g", "b") and dimension == 2  # out of the plane: one number
                ok = (
                    isinstance(value, (int, float))
                    if second_2d
                    else (isinstance(value, list) and len(value) == dimension)
                )
                if not ok or isinstance(value, bool):
                    shape = "a number" if second_2d else f"a list of {dimension} numbers"
                    raise UniverseError(f"'universe.background.{key}' must be {shape}")

        boundary, box = block.get("boundary", "open"), block.get("box")
        if boundary not in Environment.BOUNDARIES:
            raise UniverseError(f"'universe.boundary' must be one of {list(Environment.BOUNDARIES)}")
        if boundary != "open":  # the box: its lower and upper corners
            _known(box if box is not None else 0, ("lower", "upper"), "universe.box")
            try:
                Environment(boundary, box.get("lower"), box.get("upper"))
                assert len(box["lower"]) == dimension
            except (ValueError, TypeError, AssertionError):
                raise UniverseError(
                    f"'universe.box' needs 'lower' and 'upper', lists of {dimension} numbers with lower < upper"
                ) from None

        moving = block.get("moving_fields", False)
        if not isinstance(moving, bool):
            raise UniverseError("'universe.moving_fields' must be true or false")
        heat_bath = block.get("heat_bath")
        if heat_bath is not None:
            heat_bath = cls._heat_bath(heat_bath, units)
        inflow = block.get("inflow")
        if inflow is not None:
            inflow = cls._inflow(inflow, boundary, box, units)
        sources = tuple(cls._source(s, i, dimension, units) for i, s in enumerate(cls._list(block, "sources")))
        return cls(float(phi), dimension, units, boundary, background, box, sources, inflow, heat_bath, moving, frame)

    def __post_init__(self):
        if self.frame is None:  # built directly, not by from_dict: the frame of the units and the angle
            make = Frame.si if self.units == "SI" else Frame.scaled
            object.__setattr__(self, "frame", make(self.phi_bar_deg))

    @staticmethod
    def _list(block: dict, key: str) -> list:
        value = block.get(key) or []
        if not isinstance(value, (list, tuple)):
            raise UniverseError(f"'universe.{key}' must be a list")
        return list(value)

    @staticmethod
    def _source(entry, index: int, dimension: int, units: str) -> dict:
        """U6: one pinned cosmic mass and its place."""
        where = f"universe.sources[{index}]"
        _known(entry, _SOURCE, where)
        name, m, q = _cosmic_mass(entry, units, where)
        x = entry.get("x")
        if not isinstance(x, list) or len(x) != dimension:
            raise UniverseError(f"'{where}.x' must be a list of {dimension} numbers")
        return {"name": name, "m": m, "q": q, "x": [float(c) for c in x]}

    @staticmethod
    def _inflow(entry, boundary: str, box, units: str) -> dict:
        """U7, normalised: `{"name", "m", "q", "rate", "velocity", "face": {"axis", "side"}}`."""
        where = "universe.inflow"
        _known(entry, _INFLOW, where)
        if boundary == "open":
            raise UniverseError(f"'{where}': the inflow enters a box; set 'universe.boundary' and 'universe.box'")
        name, m, q = _cosmic_mass(entry, units, where)
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
            make_inflow(out, box)
        except (ValueError, TypeError) as exc:
            raise UniverseError(f"'{where}': {exc}") from None
        out["rate"], out["velocity"] = float(out["rate"]), [float(c) for c in out["velocity"]]
        return out

    @staticmethod
    def _heat_bath(entry, units: str) -> dict:
        _known(entry, ("temperature", "collision_rate"), "universe.heat_bath")
        try:
            HeatBath(entry.get("temperature"), entry.get("collision_rate"), K_B[units])
        except (ValueError, TypeError):
            raise UniverseError(
                "'universe.heat_bath' needs a positive 'temperature' and a positive 'collision_rate'"
            ) from None
        return {"temperature": float(entry["temperature"]), "collision_rate": float(entry["collision_rate"])}

    # ------------------------------------------------------------------ reading
    def to_dict(self) -> dict:
        """The `universe` block with every default filled in (the form `Settings.universe` holds).
        `sources` is listed only when there are some, so that universes without them read as before."""
        out = {
            "phi_bar_deg": self.phi_bar_deg,
            "dimension": self.dimension,
            "units": self.units,
            "boundary": self.boundary,
            "background": self.background,
            "box": self.box,
            "inflow": self.inflow,
            "heat_bath": self.heat_bath,
            "moving_fields": self.moving_fields,
        }
        if self.sources:
            out["sources"] = [dict(s) for s in self.sources]
        return out

    @property
    def constants(self) -> Constants:
        return SI if self.units == "SI" else scaled()

    @property
    def k_b(self) -> float:
        return K_B[self.units]

    def environment(self, t0: float = 0.0) -> Environment:
        """The walls, the inflow and the heat bath of this universe, the inflow counting from `t0`."""
        box = self.box or {}
        return Environment(
            self.boundary,
            box.get("lower"),
            box.get("upper"),
            inflow=make_inflow(self.inflow, box, t0=t0) if self.inflow else None,
            heat_bath=make_heat_bath(self.heat_bath, self.units) if self.heat_bath else None,
        )

    # ------------------------------------------------------------------ variants
    def with_(self, **changes) -> "Universe":
        """The same universe with some settings changed, validated again (a new object)."""
        block = {key: value for key, value in self.to_dict().items() if value is not None}
        block.update(changes)
        return Universe.from_dict(block)

    def angle_sweep(self, start: float = 10.0, stop: float = 170.0, step: float = 5.0) -> list:
        """U1 "sweep": this universe at the frame angles `start`, `start + step`, ... up to `stop`."""
        if not (step > 0 and stop >= start):
            raise UniverseError("an angle sweep needs step > 0 and stop >= start")
        count = int((stop - start) / step + 1e-9) + 1
        return [self.with_(phi_bar_deg=start + k * step) for k in range(count)]

    def in_units(self, units: str) -> "Universe":
        """U3 "side by side": a universe of the same dimension in the other units, at that
        system's default frame angle. Lengths, fields and the box are NOT converted: a scaled
        universe has its own numbers, so this is refused when any of them is set."""
        if units not in UNITS:
            raise UniverseError("'units' must be 'SI' or 'scaled'")
        if units == self.units:
            return self
        if self.box or self.background != "none" or self.sources or self.inflow or self.heat_bath:
            raise UniverseError(
                "a universe with a box, background fields, sources, an inflow or a heat bath has no "
                "automatic twin in other units: its numbers must be given in those units"
            )
        return replace(
            Universe.from_dict({"units": units, "dimension": self.dimension}), moving_fields=self.moving_fields
        )
