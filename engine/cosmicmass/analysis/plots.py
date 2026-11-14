"""The standard plots (task E8.3): plain SVG, standard library only (no plotting library is in the
pinned environment; question 5 of `team/QUESTIONS.md`). Every figure is made from the files of one
results folder alone (`stamp.json`, `summary.json`, `timeseries*.csv`), so it can always be made
again, byte for byte (`team/RESULTS-STANDARD.md`, section 6). Axes carry units; the law and the
reading are in the caption.

    figures(folder)   # writes folder/figures/drifts.svg, trails.svg, mu_plane.svg; returns the paths
    line_plot(path, curves, x_label, y_label, caption)     # any sweep: [(name, xs, ys), ...]
"""

import csv
import json
import math
from pathlib import Path

from ..constants import SI

__all__ = ["figures", "line_plot", "scatter_plot"]

W, H, MARGIN = 640, 400, 60
COLOURS = ("#1f4e79", "#c0392b", "#27ae60", "#8e44ad", "#d35400", "#16a085", "#7f8c8d", "#2c3e50")


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _range(values) -> tuple:
    lo, hi = min(values), max(values)
    if lo == hi:
        pad = abs(lo) or 1.0
        return lo - pad, hi + pad
    return lo, hi


def _canvas(x_range, y_range, x_label, y_label, caption, square=False):
    (x0, x1), (y0, y1) = x_range, y_range
    if square:  # the same scale on both axes (trails, planes)
        span = max(x1 - x0, y1 - y0)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        x0, x1, y0, y1 = cx - span / 2, cx + span / 2, cy - span / 2, cy + span / 2
    pw, ph = W - 2 * MARGIN, H - 2 * MARGIN

    def to_px(x, y):
        return MARGIN + (x - x0) / (x1 - x0) * pw, H - MARGIN - (y - y0) / (y1 - y0) * ph

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H + 40}" viewBox="0 0 {W} {H + 40}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<rect x="{MARGIN}" y="{MARGIN}" width="{pw}" height="{ph}" fill="none" stroke="#444"/>',
        f'<text x="{W / 2}" y="{H - MARGIN / 3}" text-anchor="middle" font-size="13">{_escape(x_label)}</text>',
        f'<text x="16" y="{H / 2}" text-anchor="middle" font-size="13" transform="rotate(-90 16 {H / 2})">'
        f"{_escape(y_label)}</text>",
    ]
    for value, anchor, (px, py) in (
        (x0, "start", to_px(x0, y0)),
        (x1, "end", to_px(x1, y0)),
    ):
        out.append(f'<text x="{px:.1f}" y="{py + 16:.1f}" text-anchor="{anchor}" font-size="11">{value:.4g}</text>')
    for value, (px, py) in ((y0, to_px(x0, y0)), (y1, to_px(x0, y1))):
        out.append(f'<text x="{px - 4:.1f}" y="{py + 4:.1f}" text-anchor="end" font-size="11">{value:.4g}</text>')
    out.append(f'<text x="{MARGIN}" y="{H + 25}" font-size="12">{_escape(caption)}</text>')
    return out, to_px


def _write(path: Path, lines: list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines + ["</svg>"]) + "\n", encoding="utf-8")
    return path


def line_plot(path, curves, x_label: str, y_label: str, caption: str, square: bool = False) -> Path:
    """Curves `[(name, xs, ys), ...]` on common axes; a legend with the names."""
    xs = [x for _, cx, _ in curves for x in cx if math.isfinite(x)]
    ys = [y for _, _, cy in curves for y in cy if math.isfinite(y)]
    out, to_px = _canvas(_range(xs or [0.0]), _range(ys or [0.0]), x_label, y_label, caption, square)
    for k, (name, cx, cy) in enumerate(curves):
        colour = COLOURS[k % len(COLOURS)]
        points = " ".join(
            f"{px:.2f},{py:.2f}" for px, py in (to_px(x, y) for x, y in zip(cx, cy)) if math.isfinite(px + py)
        )
        out.append(f'<polyline fill="none" stroke="{colour}" stroke-width="1.5" points="{points}"/>')
        out.append(
            f'<text x="{W - MARGIN - 4}" y="{MARGIN + 16 + 15 * k}" text-anchor="end" font-size="12" '
            f'fill="{colour}">{_escape(name)}</text>'
        )
    return _write(Path(path), out)


def scatter_plot(path, points, x_label: str, y_label: str, caption: str, axes=()) -> Path:
    """Labelled points `[(name, x, y), ...]`; `axes` are lines from the origin `[(name, dx, dy), ...]`."""
    xs = [x for _, x, _ in points] + [0.0] + [dx for _, dx, _ in axes]
    ys = [y for _, _, y in points] + [0.0] + [dy for _, _, dy in axes]
    out, to_px = _canvas(_range(xs), _range(ys), x_label, y_label, caption, square=True)
    ox, oy = to_px(0.0, 0.0)
    for name, dx, dy in axes:
        px, py = to_px(dx, dy)
        out.append(
            f'<line x1="{ox:.2f}" y1="{oy:.2f}" x2="{px:.2f}" y2="{py:.2f}" stroke="#999" stroke-dasharray="4 3"/>'
        )
        out.append(f'<text x="{px:.1f}" y="{py - 4:.1f}" font-size="11" fill="#666">{_escape(name)}</text>')
    for k, (name, x, y) in enumerate(points):
        px, py = to_px(x, y)
        colour = COLOURS[k % len(COLOURS)]
        out.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="4" fill="{colour}"/>')
        out.append(f'<text x="{px + 6:.1f}" y="{py - 6:.1f}" font-size="11" fill="{colour}">{_escape(name)}</text>')
    return _write(Path(path), out)


def _rows(path: Path) -> list:
    with open(path, newline="", encoding="utf-8") as handle:
        return [{k: float(v) for k, v in row.items() if v not in ("", None)} for row in csv.DictReader(handle)]


def figures(folder) -> list:
    """The standard figures of one results folder (one run): drifts against time, trails of the
    bodies in the Real plane (when the time series has positions), and the cosmic masses of the
    bodies in the General Number plane. Written to `folder/figures/`; returns their paths."""
    folder = Path(folder)
    stamp = json.loads((folder / "stamp.json").read_text(encoding="utf-8"))
    law = stamp.get("law", {}).get("id", "?")
    units = stamp.get("universe", {}).get("units", "SI")
    unit_t, unit_x = ("s", "m") if units == "SI" else ("scaled", "scaled")
    written = []
    series = folder / "timeseries.csv"
    if series.exists():
        rows = _rows(series)
        t = [r["t"] for r in rows]
        e0 = rows[0]["energy_re"]
        drift = [abs(r["energy_re"] / e0 - 1) if e0 else abs(r["energy_re"]) for r in rows]
        mass = [abs(r["mass"] / rows[0]["mass"] - 1) if rows[0]["mass"] else 0.0 for r in rows]
        caption = f"{stamp['scenario']}, law {law}: relative change of Re(energy) and of the total mass"
        written.append(line_plot(folder / "figures" / "drifts.svg", [("energy (Re)", t, drift), ("mass", t, mass)],
                                 f"t ({unit_t})", "relative change", caption))  # fmt: skip
        bodies = sorted({int(k[1:].split("_")[0]) for k in rows[0] if k.startswith("x") and "_" in k})
        if bodies:
            curves = [(f"body {i}", [r[f"x{i}_0"] for r in rows], [r[f"x{i}_1"] for r in rows]) for i in bodies]
            caption = f"{stamp['scenario']}, law {law}: trails of the bodies in the Real plane"
            written.append(line_plot(folder / "figures" / "trails.svg", curves, f"x ({unit_x})", f"y ({unit_x})",
                                     caption, square=True))  # fmt: skip
    matter = stamp.get("matter", [])
    phi = stamp.get("universe", {}).get("phi_bar_deg")
    if matter and phi is not None:
        # each kind of body as its cosmic mass mu = m + q G, drawn at (Sh, Ht) / abs: on the unit circle
        # at the angle of mu in the plane, so that a proton and a planet can share one picture
        s = SI.s if units == "SI" else 1.0
        c, si = math.cos(math.radians(phi)), math.sin(math.radians(phi))
        points = []
        for kind in matter:
            sh, ht = kind["m"] + kind["q"] * s * c, kind["q"] * s * si
            size = math.hypot(sh, ht) or 1.0
            points.append((kind["name"] or "body", sh / size, ht / size))
        caption = f"the cosmic masses of the run in the General Number plane (frame angle {phi:g} deg), as directions"
        written.append(scatter_plot(folder / "figures" / "mu_plane.svg", points, "Sh(mu) / abs(mu)",
                                    "Ht(mu) / abs(mu)", caption, axes=[("mass axis", 1.0, 0.0),
                                    ("Composer unit G", c, si)]))  # fmt: skip
    return written
