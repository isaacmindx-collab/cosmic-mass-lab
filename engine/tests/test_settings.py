"""E5.3 (minimal): the settings loader. Every error names the bad field."""

import copy
import json

import numpy as np
import pytest

from cosmicmass.frame import Frame
from cosmicmass.laws import LawSpec
from cosmicmass.laws.l0 import L0
from cosmicmass.matter import preset
from cosmicmass.settings import SettingsError, load_settings

GOOD = {
    "scenario": "T0.1c",
    "universe": {"phi_bar_deg": 90.0, "dimension": 2, "units": "SI"},
    "law": {"id": "L0"},
    "bodies": [
        {"preset": "proton", "x": [0.0, 0.0], "fixed": True},
        {"preset": "electron", "x": [5.29177e-11, 0.0], "v": [0.0, 2.19e6]},
        {"name": "grain", "m": 1e-15, "q": 0.0, "x": [1.0, 2.0]},
        {"preset": "Earth", "q": -5e5, "x": [7e6, 0.0]},
    ],
    "numerics": {"steps": 100, "dt_initial": 1e-19},
    "kind": "mathematics",
}


def test_loads_a_dictionary_and_a_file_to_the_same_objects(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(GOOD), encoding="utf-8")
    for s in (load_settings(GOOD), load_settings(path), load_settings(str(path))):
        assert s.scenario == "T0.1c" and s.dimension == 2 and s.frame == Frame.si(90.0)
        assert s.law_spec == LawSpec() and isinstance(s.make_law(), L0)
        assert s.state.n == 4 and list(s.state.fixed) == [True, False, False, False]
        assert s.state.m[0] == preset("proton").m and s.state.q[1] == preset("electron").q
        assert np.array_equal(s.state.v, [[0, 0], [0, 2.19e6], [0, 0], [0, 0]])
        assert (s.bodies[2].name, s.state.q[3], s.bodies[3].name) == ("grain", -5e5, "Earth")
        # defaults of decision D10, and the given values
        assert s.numerics["integrator"] == "verlet" and s.numerics["adaptive"] is True
        assert s.numerics["softening_fraction"] == 1e-3 and s.numerics["steps"] == 100
        assert s.meta == {"kind": "mathematics", "preregistered": False, "producer": ""}


def test_defaults():
    s = load_settings(
        {"scenario": "x", "bodies": [{"m": 1.0, "q": 0.5, "x": [0.0, 0.0]}], "universe": {"units": "scaled"}}
    )
    assert s.frame == Frame.scaled(90.0) and s.law_spec.reading == "L0" and s.meta["kind"] == "finding"
    assert load_settings({"scenario": "x", "bodies": [{"preset": "proton", "x": [0.0, 0.0]}]}).frame == Frame.si()


def broken(path, value="__delete__", **extra):
    data = copy.deepcopy(GOOD)
    node = data
    for key in path[:-1]:
        node = node[key]
    if value == "__delete__":
        del node[path[-1]]
    else:
        node[path[-1]] = value
    return data


@pytest.mark.parametrize(
    "data, named",
    [
        (broken(["scenario"]), "scenario"),
        (broken(["bodies"]), "bodies"),
        (broken(["bodies"], []), "bodies"),
        (broken(["colour"], "red"), "colour"),
        (broken(["universe", "units"], "cgs"), "universe.units"),
        (broken(["universe", "dimension"], 4), "universe.dimension"),
        (broken(["universe", "phi_bar_deg"], 180.0), "universe.phi_bar_deg"),
        (broken(["universe", "walls"], "yes"), "walls"),
        (broken(["universe"], 3), "universe"),
        (broken(["law", "id"], "L9"), "law"),
        (broken(["law", "speed"], 1), "law"),
        (broken(["bodies", 0, "preset"], "quark"), "bodies[0].preset"),
        (broken(["bodies", 1, "x"], [0.0]), "bodies[1].x"),
        (broken(["bodies", 1, "v"], "fast"), "bodies[1].v"),
        (broken(["bodies", 2, "q"]), "bodies[2]"),
        (broken(["bodies", 0, "m"], 1.0), "bodies[0]"),
        (broken(["bodies", 0, "spin"], 1), "bodies[0]"),
        (broken(["numerics", "integrator"], "boris"), "numerics.integrator"),
        (broken(["numerics", "stepz"], 1), "stepz"),
        (broken(["kind"], "guess"), "kind"),
        (
            {"scenario": "x", "universe": {"units": "scaled"}, "bodies": [{"preset": "proton", "x": [0.0, 0.0]}]},
            "bodies[0].preset",
        ),
    ],
)
def test_errors_name_the_bad_field(data, named):
    with pytest.raises(SettingsError, match=named.replace("[", r"\[").replace("]", r"\]").replace(".", r"\.")):
        load_settings(data)
