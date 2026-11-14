"""Figures of the T1.4 demo, regenerated from the results folders alone.

    python scenarios/T1.4/figures.py results/T1.4/L0/<run-id> results/T1.4/L1a/<run-id>

Writes `figures/orbit.svg` and `figures/separation.svg` into the L1a folder, and prints the
measured separations. Uses the standard library only (the pinned environment has no
plotting library): the figures are plain SVG.
"""

import csv
import json
import math
import sys
from pathlib import Path

R0 = 5.29177e-11  # m
COLOURS = {"L0": "#1f4e9c", "L1a": "#c0392b"}
SIZE, MARGIN = 520, 60


def track(folder: Path):
    """Time and the vector from the proton to the electron, from `timeseries.csv`."""
    with open(Path(folder) / "timeseries.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    t = [float(r["t"]) for r in rows]
    x = [float(r["x1_0"]) - float(r["x0_0"]) for r in rows]
    y = [float(r["x1_1"]) - float(r["x0_1"]) for r in rows]
    return t, x, y


def _svg(curves, x_range, y_range, x_label, y_label, caption, equal=False) -> str:
    (x0, x1), (y0, y1) = x_range, y_range
    plot = SIZE - 2 * MARGIN
    px = lambda v: MARGIN + (v - x0) / (x1 - x0) * plot  # noqa: E731
    py = lambda v: SIZE - MARGIN - (v - y0) / (y1 - y0) * plot  # noqa: E731
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE + 70}" font-family="sans-serif" font-size="12">',
        f'<rect width="{SIZE}" height="{SIZE + 70}" fill="white"/>',
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{plot}" height="{plot}" fill="none" stroke="#444"/>',
    ]
    for i in range(5):
        vx, vy = x0 + i * (x1 - x0) / 4, y0 + i * (y1 - y0) / 4
        out.append(f'<text x="{px(vx):.1f}" y="{SIZE - MARGIN + 16}" text-anchor="middle">{vx:.3g}</text>')
        out.append(f'<text x="{MARGIN - 6}" y="{py(vy) + 4:.1f}" text-anchor="end">{vy:.3g}</text>')
    out.append(f'<text x="{SIZE / 2}" y="{SIZE - MARGIN + 36}" text-anchor="middle">{x_label}</text>')
    out.append(
        f'<text x="16" y="{SIZE / 2}" text-anchor="middle" transform="rotate(-90 16 {SIZE / 2})">{y_label}</text>'
    )
    for k, (name, xs, ys) in enumerate(curves):
        points = " ".join(f"{px(a):.1f},{py(b):.1f}" for a, b in zip(xs, ys))
        out.append(f'<polyline points="{points}" fill="none" stroke="{COLOURS[name]}" stroke-width="1.5"/>')
        out.append(f'<text x="{MARGIN + 10}" y="{MARGIN + 18 + 16 * k}" fill="{COLOURS[name]}">{name}</text>')
    if equal:
        out.append(f'<circle cx="{px(0):.1f}" cy="{py(0):.1f}" r="3" fill="#444"/>')
    for k, line in enumerate(caption):
        out.append(f'<text x="{MARGIN}" y="{SIZE + 14 + 15 * k}">{line}</text>')
    return "\n".join(out + ["</svg>"]) + "\n"


def make_figures(l0_folder, l1a_folder) -> list:
    """Write the two figures into `<L1a folder>/figures/`; return lines describing the motion."""
    data = {"L0": track(l0_folder), "L1a": track(l1a_folder)}
    lam = json.loads((Path(l1a_folder) / "stamp.json").read_text())["law"]["lambda"]
    scaled = {name: ([a / R0 for a in x], [b / R0 for b in y]) for name, (t, x, y) in data.items()}
    reach = 1.05 * max(max(map(abs, xs + ys)) for xs, ys in scaled.values())
    note = [
        "EXPLORATORY. Position of the electron relative to the proton.",
        f"L0: reference law. L1a: hypothesis (reading Re + lambda s Com, lambda = {lam:g}),",
        "excluded by measurement at lambda = 1 (test T9.1).",
    ]
    figures = Path(l1a_folder) / "figures"
    figures.mkdir(exist_ok=True)
    (figures / "orbit.svg").write_text(
        _svg(
            [(n, *scaled[n]) for n in ("L0", "L1a")],
            (-reach, reach),
            (-reach, reach),
            "x / r0   (r0 = 5.29177e-11 m)",
            "y / r0",
            note,
            equal=True,
        ),
        encoding="utf-8",
    )
    period = data["L0"][0][-1] / 5.0
    radial = {
        n: ([a / period for a in t], [math.hypot(a, b) / R0 for a, b in zip(x, y)]) for n, (t, x, y) in data.items()
    }
    top = 1.05 * max(max(r) for _, r in radial.values())
    note[0] = "EXPLORATORY. Separation of the pair against time."
    (figures / "separation.svg").write_text(
        _svg(
            [(n, *radial[n]) for n in ("L0", "L1a")],
            (0.0, 5.0),
            (0.0, top),
            "time / period of the L0 orbit",
            "separation / r0",
            note,
        ),
        encoding="utf-8",
    )
    lines = []
    for name, (times, r) in radial.items():
        far = max(range(len(r)), key=r.__getitem__)
        back = min(range(far, len(r)), key=r.__getitem__)
        lines.append(
            f"{name}: separation between {min(r):.4f} r0 and {max(r):.4f} r0; farthest at {times[far]:.3f} "
            f"L0 periods; nearest after that at {times[back]:.3f} L0 periods ({r[back]:.4f} r0)"
        )
    lines.append(f"figures: {figures / 'orbit.svg'}, {figures / 'separation.svg'}")
    return lines


if __name__ == "__main__":
    for line in make_figures(Path(sys.argv[1]), Path(sys.argv[2])):
        print(line)
