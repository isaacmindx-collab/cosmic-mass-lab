#!/usr/bin/env python3
"""Draw the gallery: every figure of `docs/GALLERY.md`, from the stored results.

    python tools/make_gallery.py          # writes docs/gallery/*.svg

Each figure is regenerated from the `summary.json` and time series of a results folder
(`results/<ID>/<run-id>/`), except two that the stored files cannot give and that are
recomputed with the same settings: the positions of the 200 bodies of T0.2, and the field
of one proton along a line (T0.5). Standard library only: the figures are plain SVG.
Every caption names the law and says what kind of statement the figure is.
"""

import csv
import glob
import json
import math
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "gallery"
BLUE, RED, ORANGE, GREY = "#1f4e9c", "#c0392b", "#e08e0b", "#555555"
W, H, M = 640, 520, 70  # canvas and margin of a plot


def folder(test_id: str, sub: str = "") -> Path:
    """The newest results folder of a test."""
    found = sorted(glob.glob(str(ROOT / "results" / test_id / sub / "*-*")))
    if not found:
        raise SystemExit(f"no results for {test_id}: run its scenario script first")
    return Path(found[-1])


def cases(test_id: str) -> dict:
    return json.loads((folder(test_id) / "summary.json").read_text())["cases"]


def series(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _frame(caption, height=H) -> list:
    caption = [part for line in caption for part in textwrap.wrap(line, 100)]  # the canvas holds about 100 characters
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height + 20 + 16 * len(caption)}" '
           'font-family="sans-serif" font-size="12">',
           f'<rect width="{W}" height="{height + 20 + 16 * len(caption)}" fill="white"/>']
    out += [f'<text x="{M}" y="{height + 14 + 16 * k}" font-size="11">{line}</text>' for k, line in enumerate(caption)]
    return out


def plot(name, curves, x_range, y_range, x_label, y_label, caption, dots=(), square=False):
    """Lines `(label, colour, xs, ys)` and optional points `(x, y, colour, radius)`. With
    `square`, the plot area is a square, so that a circle is drawn as a circle."""
    (x0, x1), (y0, y1) = x_range, y_range
    width = H - 2 * M if square else W - 2 * M
    left = (W - width) / 2
    px = lambda v: left + (v - x0) / (x1 - x0) * width  # noqa: E731
    py = lambda v: H - M - (v - y0) / (y1 - y0) * (H - 2 * M)  # noqa: E731
    out = _frame(caption)
    out.append(f'<rect x="{left}" y="{M}" width="{width}" height="{H - 2 * M}" fill="none" stroke="#444"/>')
    for i in range(5):
        vx, vy = x0 + i * (x1 - x0) / 4, y0 + i * (y1 - y0) / 4
        out.append(f'<text x="{px(vx):.1f}" y="{H - M + 16}" text-anchor="middle">{vx:.3g}</text>')
        out.append(f'<text x="{left - 6}" y="{py(vy) + 4:.1f}" text-anchor="end">{vy:.3g}</text>')
    out.append(f'<text x="{W / 2}" y="{H - M + 36}" text-anchor="middle">{x_label}</text>')
    out.append(f'<text x="{left - 54}" y="{H / 2}" text-anchor="middle" transform="rotate(-90 {left - 54} {H / 2})">{y_label}</text>')
    for k, (label, colour, xs, ys) in enumerate(curves):
        points = " ".join(f"{px(a):.1f},{py(b):.1f}" for a, b in zip(xs, ys))
        out.append(f'<polyline points="{points}" fill="none" stroke="{colour}" stroke-width="1.6"/>')
        out.append(f'<text x="{left + 4}" y="{M - 10 - 15 * (len(curves) - 1 - k)}" fill="{colour}">{label}</text>')  # legend above the plot
    out += [f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="{r}" fill="{colour}"/>' for x, y, colour, r in dots]
    (OUT / f"{name}.svg").write_text("\n".join(out + ["</svg>"]) + "\n", encoding="utf-8")


def bars(name, groups, unit, caption):
    """Groups `(title, [(label, value, colour), ...])`; values may be negative."""
    values = [v for _, items in groups for _, v, _ in items]
    low, high = min(0.0, min(values)), max(0.0, max(values))
    span = (high - low) * 1.2
    base = low - (span - (high - low)) / 2 if low < 0 else 0.0
    py = lambda v: H - M - (v - base) / span * (H - 2 * M)  # noqa: E731
    out = _frame(caption)
    out += [f'<line x1="{M}" y1="{py(0):.1f}" x2="{W - 20}" y2="{py(0):.1f}" stroke="#444"/>',
            f'<text x="{M}" y="{M - 30}">{unit}</text>']
    width = (W - M - 40) / (sum(len(items) for _, items in groups) + len(groups))
    x = M + 10
    for title, items in groups:
        start = x
        for label, value, colour in items:
            top, bottom = min(py(value), py(0)), max(py(value), py(0))
            out.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{width * 0.8:.1f}" height="{max(bottom - top, 1):.1f}" fill="{colour}"/>')
            out.append(f'<text x="{x + width * 0.4:.1f}" y="{top - 5 if value >= 0 else bottom + 14:.1f}" text-anchor="middle">{value:.4g}</text>')
            out.append(f'<text x="{x + width * 0.4:.1f}" y="{H - M + 16}" text-anchor="middle">{label}</text>')
            x += width
        out.append(f'<text x="{(start + x - width * 0.2) / 2:.1f}" y="{H - M + 36}" text-anchor="middle" font-weight="bold">{title}</text>')
        x += width
    (OUT / f"{name}.svg").write_text("\n".join(out + ["</svg>"]) + "\n", encoding="utf-8")


def relative(rows, scale):
    """The vector from body 0 to body 1, divided by `scale`."""
    return ([(float(r["x1_0"]) - float(r["x0_0"])) / scale for r in rows],
            [(float(r["x1_1"]) - float(r["x0_1"])) / scale for r in rows])


CHECK = "Check of the engine against mathematics, reference law L0."


def t0_figures():
    from cosmicmass.constants import SI
    from cosmicmass.fields import DirectSum
    from cosmicmass.frame import Frame
    from cosmicmass.gates import t0
    from cosmicmass.matter import preset
    from cosmicmass.runner import run
    from cosmicmass.state import State

    one, case = folder("T0.1"), cases("T0.1")
    x, y = relative(series(one / "timeseries-a.csv"), 3.844e8)
    plot("t0_1a_earth_moon", [("moon", BLUE, x, y)], (-1.2, 1.2), (-1.2, 1.2), "x / 3.844e8 m", "y / 3.844e8 m",
         ["T0.1a: the moon relative to the Earth, one orbit. " + CHECK,
          f"Period {case['a']['period'] / 86400:.3f} days; analytic two-body period {case['a']['period_analytic'] / 86400:.3f} days; criterion 27.3 days within 0.1%."],
         dots=[(0, 0, GREY, 4)], square=True)
    x, y = relative(series(one / "timeseries-b.csv"), 5.29177e-11)
    plot("t0_1b_hydrogen_like", [("electron", BLUE, x, y)], (-1.2, 1.2), (-1.2, 1.2), "x / 5.29177e-11 m", "y / 5.29177e-11 m",
         ["T0.1b: the electron relative to the proton at the Bohr radius, one orbit. " + CHECK,
          f"Period {case['b']['period']:.5e} s; criterion 1.5198e-16 s within 0.1%. Energy drift {case['b']['energy_drift']:.1e}."],
         dots=[(0, 0, GREY, 4)], square=True)
    rows, r0, p = series(one / "timeseries-c.csv"), 1e-10, preset("proton")
    strength, reduced = t0._strength(p, p), p.m / 2
    unit = math.sqrt(reduced * r0**3 / -strength)
    times = [3 * i / 60 for i in range(61)]
    plot("t0_1c_two_protons",
         [("closed form of the Coulomb escape", BLUE, times, [t0._escape_radius(t * unit, r0, strength, reduced) / r0 for t in times]),
          ("engine", RED, [float(r["t"]) / unit for r in rows], relative(rows, r0)[0])],
         (0, 3), (0, 4), "time / natural time of the pair", "separation / 1e-10 m",
         ["T0.1c: two protons released at rest. " + CHECK,
          f"The two curves lie on each other: they differ by {case['c']['separation_error']:.1e} at the end (criterion 1e-6)."])

    settings = t0.cloud_settings()  # T0.2: the stored time series has no positions; same settings, run again
    result, half = run(settings, out_root=None), 1e-7
    colour = {"electron": BLUE, "proton": RED, "neutron": GREY}
    kinds = [body["preset"] for body in settings["bodies"]]
    dots = [(pos[0] / half, pos[1] / half, colour[kind], 2.2 if kind == "electron" else 3.6) for kind, pos in zip(kinds, result.state.x)]
    drift = result.summary["conservation"]["energy_re"]
    plot("t0_2_cloud", [(f"{kinds.count(k)} {k}s", c, [], []) for k, c in colour.items()], (-1, 1), (-1, 1),
         "x / 1e-7 m (the walls are at -1 and +1)", "y / 1e-7 m",
         ["T0.2: 200 bodies in a box with reflecting walls after 10,000 steps. " + CHECK,
          f"Recomputed from the stored settings: energy drift {drift:.1e}, mass and charge exactly constant."], dots=dots, square=True)
    rows = series(folder("T0.2") / "timeseries-cloud.csv")
    e0 = float(rows[0]["energy_re"])
    plot("t0_2_energy", [("energy", BLUE, [float(r["step"]) for r in rows], [(float(r["energy_re"]) / e0 - 1) * 1e9 for r in rows])],
         (0, 10000), (-4, 4), "step", "relative change of the energy, in units of 1e-9",
         ["T0.2: energy of the 200 bodies during the run. " + CHECK,
          f"Change at the end {cases('T0.2')['cloud']['energy_drift']:.1e}; the criterion is 1e-6, 250 times the height of this plot."])

    proton, s = preset("proton"), Frame.si().s  # T0.5 along a line: the engine's field and Coulomb's law
    radii = [10 ** (-11 + 3 * i / 40) for i in range(41)]
    field = DirectSum(constants=SI).sample(State.from_bodies([proton], [[0.0, 0.0]]), [[r, 0.0] for r in radii])
    plot("t0_5_field", [("K e / r^2", BLUE, [math.log10(r) for r in radii], [math.log10(SI.K * SI.e / r**2) for r in radii])],
         (-11, -8), (6, 13), "log10 of the distance to the proton, in m", "log10 of the electric field, in V/m",
         ["T0.5: field of one proton. Line: Coulomb's law. Dots: the engine, E = -s^2 e. " + CHECK,
          f"Largest relative difference on the stored grid of 440 points: {cases('T0.5')['proton']['largest_relative_error_E']:.1e}."],
         dots=[(math.log10(r), math.log10(-s * s * e[0]), RED, 2.5) for r, e in zip(radii[::2], field.e[::2])])


def t9_and_demo_figures():
    case = cases("T9.1")["neutron"]
    bound = (abs(case["measured_in_e"]) + 2 * case["measured_standard_error_in_e"]) * 1e21
    bars("t9_1_neutron", [("in units of 1e-21 e", [("L1a, lambda = 1", abs(case["q_eff_in_e"]) * 1e21, RED),
                                                  ("measured limit (2 standard errors)", bound, BLUE)])],
         "size of the neutron's effective charge",
         ["T9.1: under the hypothesis L1a (lambda = 1) a neutron would respond as a charge of 9.009e-19 e.",
          "Measurement check: the measured charge is (-0.2 +/- 0.8)e-21 e (as cited by the book), so L1a at",
          f"this strength is excluded, and lambda must be below {case['largest_strength_allowed_at_two_standard_errors']:.4f}."])
    tracks = {law: series(folder("T1.4", law) / "timeseries.csv") for law in ("L0", "L1a")}
    r0, colours = 5.29177e-11, {"L0": BLUE, "L1a": RED}
    note = ["EXPLORATORY demo (T1.4), not a result. L0: reference law. L1a: a hypothesis (lambda = 1),",
            "excluded by measurement at this strength (T9.1)."]
    plot("t1_4_orbit", [(law, colours[law], *relative(rows, r0)) for law, rows in tracks.items()], (-3.6, 3.6), (-3.6, 3.6),
         "x / r0   (r0 = 5.29177e-11 m)", "y / r0", ["Electron relative to the proton, from the same start under two laws."] + note,
         dots=[(0, 0, GREY, 4)], square=True)
    period = float(tracks["L0"][-1]["t"]) / 5
    radial = {law: ([float(r["t"]) / period for r in rows], [math.hypot(a, b) for a, b in zip(*relative(rows, r0))])
              for law, rows in tracks.items()}
    plot("t1_4_separation", [(law, colours[law], *radial[law]) for law in tracks], (0, 5), (0, 3.6),
         "time / period of the L0 orbit", "separation / r0", ["Separation of the proton and the electron against time."] + note)
    e0 = float(tracks["L0"][0]["energy_re"])
    plot("t1_4_l0_energy", [(law, colours[law], radial[law][0], [float(r["energy_re"]) / e0 for r in rows]) for law, rows in tracks.items()],
         (0, 5), (0, 1.2), "time / period of the L0 orbit", "L0 energy / its starting value",
         ["The L0 energy of the pair. Under L1a it is not conserved: it is not the energy of that law.",
          "The engine has no energy for the Composer coordinate yet (it needs an approved derivation)."] + note)
    plot("t1_4_time_step", [(law, colours[law], radial[law][0][1:], [float(r["dt"]) / period * 1e4 for r in rows[1:]]) for law, rows in tracks.items()],
         (0, 5), (0, 16), "time / period of the L0 orbit", "time step, in units of 1e-4 L0 periods",
         ["The adaptive time step (decisions D10 and D21) during the two runs: constant on the circle,",
          "longer when the bodies are far apart and slow."] + note)


def d21_figures():
    three, runs = cases("D21.3"), folder("D21.3")
    curves = []
    for eta, label, colour in (("0.001", "eta = 1e-3", RED), ("0.0003", "eta = 3e-4", ORANGE), ("0.0001", "eta = 1e-4", BLUE)):
        rows = series(runs / f"timeseries-e=0.9,_eta={eta}.csv")
        e0, end = float(rows[0]["energy_re"]), float(rows[-1]["t"])
        curves.append((label, colour, [float(r["t"]) / end for r in rows], [abs(float(r["energy_re"]) / e0 - 1) * 1e6 for r in rows]))
    swing = [three[f"e=0.9, eta={eta}"]["largest_excursion"] for eta in ("0.001", "0.0003", "0.0001")]
    plot("d21_3_energy_excursion", curves + [("criterion 1e-6", GREY, [0, 1], [1, 1])], (0, 1), (0, 4),
         "time / length of the run", "relative change of the energy, in units of 1e-6",
         ["D21.3: energy of an eccentric orbit (e = 0.9) for three step sizes. " + CHECK,
          f"Largest swing {swing[0]:.1e}, {swing[1]:.1e}, {swing[2]:.1e}; change at the end at most {three['e=0.9, eta=0.001']['end_drift']:.1e}.",
          "The swing happens at the closest approach and comes back. Decision D21 asks for both numbers."])
    two = cases("D21.2")
    bars("d21_2_softening",
         [(title, [("step eta", two[key]["signed_error_eta"] * 1e7, BLUE), ("step eta / 2", two[key]["signed_error_eta_half"] * 1e7, ORANGE)])
          for title, key in (("softening 0", "c, softening 0"), ("softening of D10", "c, softening D10"))],
         "error of the separation of two protons against the closed form, in units of 1e-7",
         ["D21.2: with softening 0 the error shrinks when the step is halved. With the softening of D10 it",
          "grows: the softened run converges to a different answer. " + CHECK])
    four = cases("D21.4")
    bars("d21_4_speed_floor",
         [(title, [(f"floor {f}", four[f"{key}, floor {f}"]["steps"], c) for f, c in (("0.01", BLUE), ("0.1", ORANGE), ("1", RED))])
          for title, key in (("two protons flying apart", "c (protons apart)"), ("Earth and moon falling", "f (Earth-moon fall)"))],
         "number of steps of the run",
         ["D21.4: steps needed for each floor of the speed in the adaptive step. " + CHECK,
          "With floor 0 no run can start from rest. All three floors give errors of 3.8e-7 or less."])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    t0_figures()
    t9_and_demo_figures()
    d21_figures()
    for path in sorted(OUT.glob("*.svg")):
        print(path.relative_to(ROOT))
