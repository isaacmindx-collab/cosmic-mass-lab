"""E5.4: seeded population generators. Done when (docs/WORK-PLAN.md): the same seed gives identical
arrays; the measured spread matches the temperature within 1% for 10^4 bodies."""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from cosmicmass.constants import SCALED, SI
from cosmicmass.environment import K_B, kinetic_temperature
from cosmicmass.matter import preset
from cosmicmass.populations import generate
from cosmicmass.runner import run
from cosmicmass.settings import SettingsError, load_settings

ROOT = Path(__file__).resolve().parents[2]
P = preset("proton")


def settings(populations, d=3, units="SI", bodies=(), seed=7, **universe):
    return {
        "scenario": "E5.4",
        "universe": {"dimension": d, "units": units, **universe},
        "law": {"id": "L0"},
        "bodies": list(bodies),
        "populations": populations,
        "numerics": {"seed": seed, "steps": 3, "softening": 1e-9},
        "kind": "mathematics",
    }


def test_the_same_seed_gives_identical_arrays_and_another_seed_does_not():
    spec = [{"preset": "proton", "n": 50, "shape": "shell", "radius": 1.0, "width": 0.5, "temperature": 1e4}]
    a, b = load_settings(settings(spec)).state, load_settings(settings(spec)).state
    assert np.array_equal(a.x, b.x) and np.array_equal(a.v, b.v)
    c = load_settings(settings(spec, seed=8)).state
    assert not np.array_equal(a.x, c.x)


def test_the_spread_matches_the_temperature_within_one_percent():
    spec = [{"preset": "proton", "n": 10_000, "shape": "box", "lower": [0, 0, 0], "upper": [1, 1, 1],
             "temperature": 1e4}]  # fmt: skip
    state = load_settings(settings(spec)).state
    assert kinetic_temperature(state, K_B["SI"]) == pytest.approx(1e4, rel=0.01)
    sigma = math.sqrt(K_B["SI"] * 1e4 / P.m)
    assert np.std(state.v, axis=0) == pytest.approx([sigma] * 3, rel=0.02)  # each component (fewer samples each)


def test_shapes():
    rng = np.random.default_rng(1)
    box = generate({"n": 500, "shape": "box", "lower": [-1, 2], "upper": [1, 3]}, 2, SCALED, rng, (1.0, 0.0))
    assert np.all((box["x"] >= [-1, 2]) & (box["x"] <= [1, 3]))
    shell = generate({"n": 4000, "shape": "shell", "radius": 2.0, "width": 1.0, "centre": [1, 1, 1]}, 3, SCALED, rng,
                     (1.0, 0.0))  # fmt: skip
    r = np.linalg.norm(shell["x"] - 1.0, axis=1)
    assert r.min() >= 1.5 - 1e-12 and r.max() <= 2.5 + 1e-12
    # uniform in volume: the mean of r^3 is the middle of [1.5^3, 2.5^3]
    assert np.mean(r**3) == pytest.approx((1.5**3 + 2.5**3) / 2, rel=0.03)
    ring = generate({"n": 300, "shape": "ring", "radius": 5.0, "width": 0.2}, 3, SCALED, rng, (1.0, 0.0))
    rr = np.hypot(ring["x"][:, 0], ring["x"][:, 1])
    assert np.all(ring["x"][:, 2] == 0.0) and rr.min() >= 4.9 - 1e-12 and rr.max() <= 5.1 + 1e-12
    flat = generate({"n": 300, "shape": "shell", "radius": 1.0}, 2, SCALED, rng, (1.0, 0.0))
    assert np.allclose(np.linalg.norm(flat["x"], axis=1), 1.0)  # width 0: a circle


def test_keplerian_bulk_and_super_particles():
    rng = np.random.default_rng(2)
    spec = {"n": 200, "shape": "ring", "radius": 1.5e11, "width": 1e10, "keplerian": {"mass": 1.989e30},
            "bulk": [0.0, 0.0, 10.0]}  # fmt: skip
    made = generate(spec, 3, SI, rng, (1.0, 0.0))
    r = np.hypot(made["x"][:, 0], made["x"][:, 1])
    v_plane = made["v"][:, :2]
    assert np.allclose(np.linalg.norm(v_plane, axis=1), np.sqrt(SI.G_N * 1.989e30 / r), rtol=1e-12)
    cosine = np.sum(v_plane * made["x"][:, :2], axis=1) / (np.linalg.norm(v_plane, axis=1) * r)
    assert np.max(np.abs(cosine)) < 1e-12  # perpendicular to the radius
    assert np.all(made["x"][:, 0] * v_plane[:, 1] - made["x"][:, 1] * v_plane[:, 0] > 0)  # counter-clockwise
    assert np.all(made["v"][:, 2] == 10.0)  # the bulk flow
    heavy = generate({"n": 5000, "shape": "box", "lower": [0, 0], "upper": [1, 1], "temperature": 2.0, "weight": 1e3},
                     2, SCALED, rng, (0.5, -0.25))  # fmt: skip
    assert np.all(heavy["m"] == 500.0) and np.all(heavy["q"] == -250.0)  # the same charge-to-mass ratio
    assert np.std(heavy["v"]) == pytest.approx(math.sqrt(2.0 / 0.5), rel=0.03)  # the real particle's speeds


def test_a_run_with_populations_and_its_stamp(tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import validate_results

    spec = [
        {"preset": "proton", "n": 4, "shape": "box", "temperature": 300.0},
        {"preset": "electron", "n": 3, "shape": "ring", "radius": 1e-7, "centre": [5e-7, 5e-7], "weight": 2.0},
    ]
    box = {"lower": [0.0, 0.0], "upper": [1e-6, 1e-6]}
    data = settings(spec, d=2, bodies=[{"preset": "neutron", "x": [1e-7, 1e-7]}], boundary="reflecting", box=box)
    loaded = load_settings(data)
    assert loaded.state.n == 8 and loaded.state.m[0] == preset("neutron").m  # listed bodies first
    assert np.all(loaded.state.q[5:] == 2 * preset("electron").q)
    result = run(data, out_root=tmp_path)
    stamp = json.loads((result.folder / "stamp.json").read_text(encoding="utf-8"))
    assert stamp["populations"] == spec and {k["name"]: k["n"] for k in stamp["matter"]} == {
        "neutron": 1,
        "proton": 4,
        "electron": 3,
    }
    assert validate_results.validate_folder(result.folder) == []
    only = load_settings(settings([{"m": 1.0, "q": 0.0, "n": 2, "shape": "shell", "radius": 1.0}], units="scaled"))
    assert only.state.n == 2
    plain = settings([], d=2, bodies=[{"preset": "proton", "x": [0.0, 0.0]}])
    plain["numerics"]["dt_max"] = 1e-9  # a lone body at rest gives no step of its own
    assert "populations" not in run(plain, out_root=None).stamp  # without populations, no key in the stamp


@pytest.mark.parametrize(
    "population,message",
    [
        ({"preset": "proton", "n": 0}, "positive whole"),
        ({"preset": "proton", "n": 2, "shape": "cube"}, "shape"),
        ({"preset": "quark", "n": 2}, "unknown preset"),
        ({"n": 2}, "give a 'preset'"),
        ({"preset": "proton", "n": 2, "colour": 1}, "unknown field"),
        ({"preset": "proton", "n": 2, "shape": "box"}, "lower"),  # no box in the universe, none given
        ({"preset": "proton", "n": 2, "lower": [1, 1, 1], "upper": [0, 2, 2]}, "below upper"),
        ({"preset": "proton", "n": 2, "shape": "shell"}, "radius"),
        ({"preset": "proton", "n": 2, "shape": "ring", "radius": 1.0, "width": 3.0}, "radius"),
        ({"preset": "proton", "n": 2, "lower": [0] * 3, "upper": [1] * 3, "temperature": -1}, "temperature"),
        ({"preset": "proton", "n": 2, "lower": [0] * 3, "upper": [1] * 3, "weight": 0}, "weight"),
        ({"preset": "proton", "n": 2, "lower": [0] * 3, "upper": [1] * 3, "bulk": [1, 2]}, "bulk"),
        ({"preset": "proton", "n": 2, "shape": "ring", "radius": 1.0, "keplerian": {"mass": -1}}, "keplerian"),
    ],
)
def test_bad_populations_are_refused(population, message):
    with pytest.raises(SettingsError, match=message):
        load_settings(settings([population]))


def test_bodies_or_populations_are_needed():
    with pytest.raises(SettingsError, match="bodies"):
        load_settings(settings([]))


def test_super_particles_and_temperature_review_of_66():
    # a super-particle moves at the real particle's thermal speeds but carries `weight` times its mass,
    # so the temperature from the bodies' own masses is `weight` times the population's (review of #66)
    box = {"shape": "box", "lower": [0.0, 0.0, 0.0], "upper": [1.0, 1.0, 1.0], "temperature": 1e4}
    plain = load_settings(settings([{"preset": "neutron", "n": 4000, **box}]))
    heavy = load_settings(settings([{"preset": "neutron", "n": 4000, "weight": 1e6, **box}]))
    t_plain, t_heavy = (kinetic_temperature(s.state, K_B["SI"]) for s in (plain, heavy))
    assert t_heavy == pytest.approx(1e6 * t_plain, rel=1e-12)  # the same draws, a million times the mass
    # a heat bath would drive them to the wrong speeds: refused
    bath = {"heat_bath": {"temperature": 1e4, "collision_rate": 1.0}}
    with pytest.raises(SettingsError, match="heat_bath"):
        load_settings(settings([{"preset": "neutron", "n": 10, "weight": 2.0, **box}], **bath))
    load_settings(settings([{"preset": "neutron", "n": 10, **box}], **bath))  # weight 1: allowed
    # the summary says how to read the temperature, only when a population is weighted
    labelled = run(settings([{"preset": "neutron", "n": 5, "weight": 3.0, **box}]), out_root=None)
    assert labelled.summary["super_particles"]["weights"] == [3.0]
    assert "divide by" in labelled.summary["super_particles"]["note"]
    assert run(settings([{"preset": "neutron", "n": 5, **box}]), out_root=None).summary["super_particles"] is None


def test_keplerian_speed_of_a_body_on_the_axis_is_zero_not_nan():
    rng = np.random.default_rng(0)
    spec = {"n": 3, "shape": "box", "lower": [-1.0, -1.0], "upper": [1.0, 1.0], "keplerian": {"mass": 1.0}}
    from cosmicmass import populations

    x = np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 2.0]])
    v = populations.velocities(spec, x, 1.0, SCALED, rng)
    assert np.all(np.isfinite(v))
    assert list(v[0]) == [0.0, 0.0]  # on the axis: no circular direction, no speed
    assert v[1] == pytest.approx([0.0, 1.0]) and v[2] == pytest.approx([-math.sqrt(0.5), 0.0])
