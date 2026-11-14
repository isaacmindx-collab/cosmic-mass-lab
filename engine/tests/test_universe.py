"""E5.2: `Universe`, the settings U1 to U8 of docs/05-scenarios-and-tests.md, and the rest of E5.3
(the named laws). Done when: every U option can be expressed; invalid combinations are refused."""

import json
import math
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.constants import SI
from cosmicmass.environment import Environment
from cosmicmass.frame import DEFAULT_PHI_BAR_DEG
from cosmicmass.gates import t0
from cosmicmass.matter import preset
from cosmicmass.runner import run
from cosmicmass.settings import DEFAULT_EXPLORATORY_LAW, SettingsError, load_settings
from cosmicmass.universe import Universe, UniverseError

ROOT = Path(__file__).resolve().parents[2]
BOX = {"lower": [0.0, 0.0], "upper": [1.0, 2.0]}
INFLOW = {"preset": "neutron", "rate": 10.0, "velocity": [1.0, 0.0], "face": {"axis": 0, "side": "lower"}}


def test_defaults_and_the_dictionary_form():
    u = Universe.from_dict()
    assert (u.phi_bar_deg, u.dimension, u.units, u.boundary, u.background) == (
        DEFAULT_PHI_BAR_DEG,
        2,
        "SI",
        "open",
        "none",
    )
    assert u.box is None and u.sources == () and u.inflow is None and u.heat_bath is None and u.moving_fields is False
    assert (
        u.frame.phi_bar_deg == pytest.approx(DEFAULT_PHI_BAR_DEG, rel=1e-14)
        and u.constants is SI
        and u.frame.s == pytest.approx(SI.s)
    )
    assert Universe.from_dict({}) == u and Universe.from_dict(u.to_dict() | {"box": None}) == u
    block = u.to_dict()  # the form Settings.universe holds: every key, and no "sources" when there are none
    assert set(block) == {"phi_bar_deg", "dimension", "units", "boundary", "background", "box", "inflow"} | {
        "heat_bath",
        "moving_fields",
    }
    scaled = Universe.from_dict({"units": "scaled"})  # U3; the default angle of scaled units is 90 degrees
    assert scaled.phi_bar_deg == 90.0 and scaled.frame.s == 1.0 and scaled.constants.G_N == 1.0 and scaled.k_b == 1.0
    direct = Universe(phi_bar_deg=120.0, units="scaled")  # built directly: the frame follows
    assert direct.frame.phi_bar_deg == pytest.approx(120.0) and direct.frame.s == 1.0


def test_every_u_option_of_the_test_plan_can_be_expressed():
    # U1: 79.86, 90 and 10.14 degrees, and the sweep 10..170 in steps of 5
    for angle in (79.86, 90.0, 10.14):
        assert Universe.from_dict({"phi_bar_deg": angle}).frame.phi_bar_deg == pytest.approx(angle, rel=1e-14)
    sweep = Universe.from_dict({"dimension": 3}).angle_sweep()
    assert [u.phi_bar_deg for u in sweep] == [10.0 + 5 * k for k in range(33)] and sweep[-1].phi_bar_deg == 170.0
    assert all(u.dimension == 3 for u in sweep) and len(Universe.from_dict().angle_sweep(45.0, 90.0, 45.0)) == 2
    # U2: 2D (motion in a plane with the 1/r^2 field: the slice of 3D, D21) and 3D
    assert [Universe.from_dict({"dimension": d}).dimension for d in (2, 3)] == [2, 3]
    # U3: SI, scaled, and both side by side
    si = Universe.from_dict({"phi_bar_deg": 79.86})
    pair = (si, si.in_units("scaled"))
    assert [u.units for u in pair] == ["SI", "scaled"] and si.in_units("SI") is si and pair[1].phi_bar_deg == 90.0
    # U4: every boundary the environment knows (wrap-around arrives with D36)
    for boundary in Environment.BOUNDARIES:
        u = Universe.from_dict({"boundary": boundary, "box": None if boundary == "open" else BOX})
        assert u.boundary == boundary and u.environment().boundary == boundary
    # U5: none, and each uniform field, in 2D and in 3D
    for field in ("g", "e"):
        assert Universe.from_dict({"background": {field: [0.0, -9.8]}}).background == {field: [0.0, -9.8]}
    for field in ("B_g", "b"):
        assert Universe.from_dict({"background": {field: 2.0}}).background == {field: 2.0}
        assert Universe.from_dict({"dimension": 3, "background": {field: [0.0, 0.0, 2.0]}}).dimension == 3
    # U6: fixed sources, by preset or by m and q
    u = Universe.from_dict({"sources": [{"preset": "Earth", "x": [0.0, 0.0]}, {"m": 2.0, "q": 1e-9, "x": [1.0, 1.0]}]})
    assert u.sources[0] == {"name": "Earth", "m": preset("Earth").m, "q": 0.0, "x": [0.0, 0.0]}
    assert u.sources[1]["m"] == 2.0 and u.to_dict()["sources"][1]["x"] == [1.0, 1.0]
    # U7: an inflow through one face of a box, and a heat bath
    u = Universe.from_dict(
        {
            "boundary": "reflecting",
            "box": BOX,
            "inflow": INFLOW,
            "heat_bath": {"temperature": 300, "collision_rate": 1e9},
        }
    )
    assert u.inflow["name"] == "neutron" and u.inflow["rate"] == 10.0 and u.heat_bath["temperature"] == 300.0
    env = u.environment(t0=2.0)
    assert env.inflow.t0 == 2.0 and env.inflow.m == preset("neutron").m and env.heat_bath.temperature == 300.0
    # E2.2: the second field of moving bodies
    assert Universe.from_dict({"moving_fields": True}).moving_fields is True


@pytest.mark.parametrize(
    "block,named",
    [
        ({"colour": "blue"}, "colour"),
        ({"units": "cgs"}, "universe.units"),
        ({"dimension": 4}, "universe.dimension"),
        ({"dimension": True}, "universe.dimension"),
        ({"phi_bar_deg": 0.0}, "universe.phi_bar_deg"),
        ({"phi_bar_deg": "steep"}, "universe.phi_bar_deg"),
        ({"background": "strong"}, "universe.background"),
        ({"background": {"h": [0.0, 0.0]}}, "universe.background"),
        ({"background": {"g": [0.0, 0.0, 1.0]}}, "universe.background.g"),  # three numbers in 2D
        ({"background": {"b": [0.0, 0.0, 1.0]}}, "universe.background.b"),  # in 2D the second field is one number
        ({"dimension": 3, "background": {"B_g": 1.0}}, "universe.background.B_g"),
        ({"background": {"b": True}}, "universe.background.b"),
        ({"boundary": "wrap-around"}, "universe.boundary"),
        ({"boundary": "reflecting"}, "universe.box"),  # walls without a box
        ({"boundary": "reflecting", "box": {"lower": [0.0, 0.0], "upper": [1.0, 0.0]}}, "universe.box"),
        ({"boundary": "absorbing", "box": {"lower": [0.0] * 3, "upper": [1.0] * 3}}, "universe.box"),  # 3 numbers in 2D
        ({"boundary": "reflecting", "box": {"lower": [0.0, 0.0], "top": [1.0, 1.0]}}, "universe.box"),
        ({"inflow": INFLOW}, "enters a box"),  # an inflow into an open universe
        ({"boundary": "reflecting", "box": BOX, "inflow": dict(INFLOW, velocity=[-1.0, 0.0])}, "universe.inflow"),
        ({"units": "scaled", "boundary": "reflecting", "box": BOX, "inflow": INFLOW}, "SI only"),
        ({"boundary": "reflecting", "box": BOX, "inflow": dict(INFLOW, preset="quark")}, "unknown preset"),
        ({"heat_bath": {"temperature": -1.0, "collision_rate": 1.0}}, "universe.heat_bath"),
        ({"moving_fields": "yes"}, "universe.moving_fields"),
        ({"sources": {"m": 1.0}}, "universe.sources"),
        ({"sources": [{"m": 1.0, "x": [0.0, 0.0]}]}, "universe.sources[0]"),
        ({"sources": [{"preset": "Earth", "x": [0.0]}]}, "universe.sources[0].x"),
        (
            {"sources": [{"preset": "Earth", "x": [0.0, 0.0], "v": [1.0, 0.0]}]},
            "universe.sources[0]",
        ),  # a source is pinned
        ({"sources": ["Earth"]}, "universe.sources[0]"),
    ],
)
def test_invalid_universes_are_refused_and_the_error_names_the_field(block, named):
    with pytest.raises(UniverseError, match=named.replace("[", r"\[").replace("]", r"\]")):
        Universe.from_dict(block)
    with pytest.raises(
        SettingsError, match=named.replace("[", r"\[").replace("]", r"\]")
    ):  # the same through the loader
        load_settings({"scenario": "x", "universe": block, "bodies": [{"m": 1.0, "q": 0.0, "x": [0.5, 0.5]}]})


def test_variants_are_validated_again():
    u = Universe.from_dict({"boundary": "reflecting", "box": BOX})
    assert u.with_(phi_bar_deg=45.0).frame.phi_bar_deg == pytest.approx(45.0) and u.with_(phi_bar_deg=45.0).box == BOX
    assert u.with_(boundary="absorbing").boundary == "absorbing" and u.boundary == "reflecting"  # a new object
    with pytest.raises(UniverseError, match="universe.dimension"):
        u.with_(dimension=5)
    with pytest.raises(UniverseError, match="universe.box"):
        u.with_(dimension=3)  # the box has two numbers
    with pytest.raises(UniverseError, match="step > 0"):
        u.angle_sweep(step=0.0)
    with pytest.raises(UniverseError, match="no\\s+automatic twin"):
        u.in_units("scaled")  # the box is in metres: its numbers are not converted
    with pytest.raises(UniverseError, match="'units'"):
        Universe.from_dict().in_units("cgs")
    moving = Universe.from_dict({"moving_fields": True, "dimension": 3}).in_units("scaled")
    assert moving.moving_fields is True and moving.dimension == 3 and moving.units == "scaled"
    with pytest.raises(AttributeError):
        u.dimension = 3  # a universe does not change


def test_the_loader_builds_the_universe_and_keeps_the_dictionary():
    data = {
        "scenario": "x",
        "universe": {"units": "scaled", "boundary": "reflecting", "box": BOX},
        "bodies": [{"m": 1.0, "q": 0.0, "x": [0.5, 0.5]}],
    }
    s = load_settings(data)
    assert isinstance(s.world, Universe) and s.universe == s.world.to_dict() and s.frame is s.world.frame
    assert s.universe["boundary"] == "reflecting" and s.universe["phi_bar_deg"] == 90.0 and s.dimension == 2
    assert "sources" not in s.universe and data["universe"] == {"units": "scaled", "boundary": "reflecting", "box": BOX}


def test_fixed_sources_of_the_universe_become_pinned_bodies(tmp_path):
    data = {
        "scenario": "fall",
        "universe": {"sources": [{"preset": "Earth", "x": [0.0, 0.0]}]},
        "bodies": [{"preset": "proton", "x": [7e6, 0.0]}],
        "numerics": {"steps": 20, "softening": 0.0},
        "kind": "mathematics",
    }
    s = load_settings(data)
    assert s.state.n == 2 and list(s.state.fixed) == [False, True] and s.state.m[1] == preset("Earth").m
    assert [b.name for b in s.bodies] == ["proton", "Earth"] and not s.state.v[1].any()
    as_body = dict(data, universe={}, bodies=data["bodies"] + [{"preset": "Earth", "x": [0.0, 0.0], "fixed": True}])
    a, b = run(data, out_root=tmp_path), run(as_body, out_root=None)
    assert np.array_equal(a.state.x, b.state.x) and a.summary["final"] == b.summary["final"]  # the same run
    assert a.state.x[1].tolist() == [0.0, 0.0] and a.state.x[0, 0] < 7e6  # the Earth stays, the proton falls
    stamp = json.loads((a.folder / "stamp.json").read_text(encoding="utf-8"))
    assert {"name": "Earth", "m": preset("Earth").m, "q": 0.0, "n": 1} in stamp["matter"]
    assert "sources" not in stamp["universe"]  # the stamp names them as matter
    only = load_settings({"scenario": "x", "universe": {"sources": [{"m": 1.0, "q": 0.0, "x": [0.0, 0.0]}]}})
    assert only.state.n == 1 and only.state.fixed[0]  # a universe of sources only loads
    with pytest.raises(SettingsError, match="non-empty"):
        load_settings({"scenario": "x"})
    with pytest.raises(SettingsError, match="must be lists"):
        load_settings({"scenario": "x", "bodies": {"m": 1.0}})


def test_named_laws_and_the_default_exploratory_law():
    body = {"scenario": "x", "bodies": [{"m": 1.0, "q": 0.0, "x": [0.0, 0.0]}]}
    assert load_settings(body).law_spec.reading == "L0"  # no law: the reference law
    assert load_settings(dict(body, law="reference")).law_spec.to_dict() == load_settings(body).law_spec.to_dict()
    exploratory = load_settings(dict(body, law="exploratory")).law_spec
    assert (
        exploratory.to_dict()
        == DEFAULT_EXPLORATORY_LAW
        == load_settings(dict(body, law={"id": "L1a"})).law_spec.to_dict()
    )
    text = (ROOT / "docs" / "05-scenarios-and-tests.md").read_text(encoding="utf-8")  # as the test plan states it
    assert (
        "**Default exploratory law:** L1a, sign +, lambda = 1, radial, all terms, L6 off, inertia `Re(mu)`, 1/r^2."
        in text
    )
    assert (exploratory.reading, exploratory.sign, exploratory.strength, exploratory.direction) == (
        "L1a",
        "+",
        1.0,
        "radial",
    )
    assert (exploratory.terms, exploratory.moving, exploratory.inertia, exploratory.range) == (
        "all",
        "off",
        "Re",
        "1/r^2",
    )
    with pytest.raises(SettingsError, match="unknown name 'newton'"):
        load_settings(dict(body, law="newton"))
    assert math.isclose(
        load_settings(dict(body, law="exploratory")).make_law().strength(load_settings(body).frame), 1.0
    )


def test_settings_load_to_the_same_objects(tmp_path):
    """E5.3's done-when: each scenario's settings load to the same objects, from a file and from a
    dictionary. The scenarios of the gates build their settings in code (`gates/t0.py`); the
    scaffold writes a file (`tools/new_scenario.py`). Both kinds are loaded here."""
    cases = [
        t0.cloud_settings(n=20, steps=10),
        t0._pair("pair", preset("Earth"), preset("moon"), 3.844e8, 1.0e3, 79.86, {}),
    ]
    cases += [
        json.loads(path.read_text(encoding="utf-8")) for path in sorted((ROOT / "scenarios").glob("*/settings.json"))
    ]
    for k, data in enumerate(cases):
        path = tmp_path / f"settings-{k}.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        a, b = load_settings(path), load_settings(data)
        assert a.universe == b.universe and a.world == b.world and a.law_spec == b.law_spec and a.numerics == b.numerics
        assert a.meta == b.meta and a.scenario == b.scenario
        for name in ("m", "q", "x", "v", "fixed", "alive"):
            assert np.array_equal(getattr(a.state, name), getattr(b.state, name))
