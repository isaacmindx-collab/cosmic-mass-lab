"""E8: diagnostics (temperature, pressure on the walls), the convergence helper, the standard plots."""

import math

import numpy as np
import pytest

from cosmicmass.analysis.convergence import convergence
from cosmicmass.analysis.plots import figures, line_plot, scatter_plot
from cosmicmass.runner import run, wall_pressure


def gas(n=300, side=10.0, seed=4, t_end=120.0):
    """A dilute 2D gas of very light, neutral bodies (gravity negligible) in a reflecting box, scaled units,
    velocities drawn at temperature 1 (k_B = 1)."""
    rng = np.random.default_rng(seed)
    bodies = [
        {"m": 1e-12, "q": 0.0, "x": list(rng.uniform(0.5, side - 0.5, 2)), "v": list(rng.normal(0.0, 1e6, 2))}
        for _ in range(n)
    ]  # k_B T / m = 1 / 1e-12: the speed spread is 1e6
    return {
        "scenario": "E8-gas",
        "universe": {"units": "scaled", "dimension": 2, "boundary": "reflecting",
                     "box": {"lower": [0.0, 0.0], "upper": [side, side]}},
        "law": {"id": "L0"},
        "bodies": bodies,
        "numerics": {"adaptive": False, "dt_initial": t_end / 2000 / 1e6, "steps": 2000, "softening": 0.0},
        "kind": "mathematics",
    }  # fmt: skip


def test_pressure_on_the_walls_is_n_k_t():
    # kinetic theory in 2D: the momentum given to the walls per time and per length is N k_B T / A
    settings = gas()
    result = run(settings, out_root=None)
    walls = result.summary["walls"]
    temperature = result.summary["final"]["temperature"]  # E8.1: sum m v^2 / (d N k_B)
    assert temperature == pytest.approx(result.summary["initial"]["temperature"], rel=1e-9)  # no force to speak of
    expected = 300 * temperature / 10.0**2
    assert walls["pressure_mean"] == pytest.approx(expected, rel=0.05)
    assert set(walls["pressure"]) == {"0-lower", "0-upper", "1-lower", "1-upper"}
    for value in walls["pressure"].values():
        assert value == pytest.approx(expected, rel=0.15)  # each wall, with fewer hits
    assert result.summary["wall_hits"] > 5000


def test_wall_pressure_by_hand():
    box = {"lower": [0.0, 0.0, 0.0], "upper": [1.0, 2.0, 4.0]}
    out = wall_pressure(box, {"0-lower": 16.0, "2-upper": 4.0}, elapsed=2.0)
    assert out["pressure"]["0-lower"] == pytest.approx(16.0 / (2.0 * 8.0))  # the face of axis 0: 2 x 4
    assert out["pressure"]["2-upper"] == pytest.approx(4.0 / (2.0 * 2.0)) and out["pressure"]["1-lower"] == 0.0
    assert out["pressure_mean"] == pytest.approx(20.0 / (2.0 * 2 * (8.0 + 4.0 + 2.0)))
    assert wall_pressure({}, {}, 1.0) is None and wall_pressure(box, {}, 0.0) is None


def kepler(eta=1e-3):
    return {
        "scenario": "E8-kepler",
        "universe": {"units": "scaled", "dimension": 2},
        "law": {"id": "L0"},
        "bodies": [{"m": 1.0, "q": 0.0, "x": [-0.5, 0.0], "v": [0.0, -0.5]},
                   {"m": 1.0, "q": 0.0, "x": [0.5, 0.0], "v": [0.0, 0.5]}],
        "numerics": {"t_end": 0.25 * math.pi, "eta": eta, "softening": 0.0},  # an eighth of an orbit
        "kind": "mathematics",
    }  # fmt: skip


def separation(result):
    return {"separation": float(np.linalg.norm(result.state.x[1] - result.state.x[0])),
            "x0": float(result.state.x[0, 0])}  # fmt: skip


def test_convergence_helper():
    block = convergence(kepler(), separation)
    assert set(block["step"]) == {"step", "step/2", "step/4"}
    assert block["converged"] and block["largest_change"] < 1e-6  # a circular orbit: second order
    assert block["change_step_half_to_quarter"]["x0"] < block["change_step_to_half"]["x0"]  # it shrinks

    # body counts, through the scenario's own resize
    def resize(settings, n):
        settings["bodies"] = settings["bodies"][:2] + [
            {"m": 1e-9, "q": 0.0, "x": [5.0 + k, 5.0], "v": [0.0, 0.0]} for k in range(n - 2)
        ]
        return settings

    block = convergence(kepler(), separation, counts=(3, 4), resize=resize)
    assert set(block["counts"]) == {"3", "4"} and block["converged"]
    with pytest.raises(ValueError, match="resize"):
        convergence(kepler(), separation, counts=(3,))
    fixed = kepler()
    fixed["numerics"] = {"adaptive": False, "dt_initial": 1e-3, "t_end": 1.0, "softening": 0.0}
    assert convergence(fixed, separation)["converged"]
    loose = convergence(kepler(eta=0.3), separation, tolerance=1e-12)
    assert loose["converged"] is False


def test_figures_from_a_results_folder_alone(tmp_path):
    result = run(kepler(), out_root=tmp_path)
    written = figures(result.folder)
    assert sorted(p.name for p in written) == ["drifts.svg", "mu_plane.svg", "trails.svg"]
    first = {p.name: p.read_bytes() for p in written}
    assert all(b.startswith(b"<svg") and b.rstrip().endswith(b"</svg>") for b in first.values())
    again = figures(result.folder)  # made again from the folder alone: the same bytes
    assert {p.name: p.read_bytes() for p in again} == first
    # a run with an inflow has no positions in its time series: no trails, the rest is drawn
    settings = kepler()
    settings["scenario"] = "E8-inflow"  # another run id: two runs of one scenario in one second would collide
    settings["universe"] = {"units": "SI", "dimension": 2, "boundary": "reflecting",
                            "box": {"lower": [0.0, 0.0], "upper": [1e-6, 1e-6]},
                            "inflow": {"preset": "proton", "rate": 1e9, "velocity": [1e3, 0.0],
                                       "face": {"axis": 0, "side": "lower"}}}  # fmt: skip
    settings["bodies"] = [{"preset": "electron", "x": [5e-7, 5e-7], "fixed": True}]
    settings["numerics"] = {"adaptive": False, "dt_initial": 1e-10, "steps": 20, "softening": 1e-9}
    names = sorted(p.name for p in figures(run(settings, out_root=tmp_path).folder))
    assert names == ["drifts.svg", "mu_plane.svg"]


def test_plot_helpers(tmp_path):
    path = line_plot(tmp_path / "sweep.svg", [("a", [0, 1, 2], [1, 4, 9]), ("b <&>", [0, 2], [0, 0])],
                     "angle (deg)", "steps", "a sweep")  # fmt: skip
    text = path.read_text(encoding="utf-8")
    assert text.count("<polyline") == 2 and "b &lt;&amp;&gt;" in text
    flat = line_plot(tmp_path / "flat.svg", [("c", [1, 1], [2, 2])], "x", "y", "one point")
    assert "<polyline" in flat.read_text(encoding="utf-8")
    dots = scatter_plot(tmp_path / "dots.svg", [("p", 1.0, 0.5)], "x", "y", "c", axes=[("axis", 1.0, 0.0)])
    assert dots.read_text(encoding="utf-8").count("<circle") == 1
