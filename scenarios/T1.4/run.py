"""T1.4, the demo of version 0.1.0: a hydrogen-like pair under L0 and under L1a.

EXPLORATORY (decision D12): not pre-registered as a result, never to be cited. L0 is the
reference law. L1a is a hypothesis, and at lambda = 1 it is excluded by measurement (T9.1);
the demo shows what the engine does with a reading, not what nature does.
Notebook: team/notes/T1.4.md.

    python scenarios/T1.4/run.py        # writes results/T1.4/<law>/<run-id>/ and the figures
"""

import math
import sys
from pathlib import Path

from cosmicmass.constants import SI
from cosmicmass.matter import preset
from cosmicmass.runner import run

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figures import make_figures  # noqa: E402

PRODUCER = "Claude chat session on claude.ai / Claude Fable 5.2 (sponsor @MostafaDerraz)"
R0 = 5.29177e-11  # m, the Bohr radius
PERIODS = 5.0  # periods of the L0 orbit


def settings(law: dict, producer: str) -> dict:
    p, e = preset("proton"), preset("electron")
    strength = SI.G_N * p.m * e.m - SI.K * p.q * e.q  # G_N Re(mu_p mu_e): the pull of L0
    total, reduced = p.m + e.m, p.m * e.m / (p.m + e.m)
    speed = math.sqrt(strength / (reduced * R0))  # circular speed of L0
    period = 2 * math.pi * math.sqrt(reduced * R0**3 / strength)
    bodies = [
        {"preset": "proton", "x": [-e.m / total * R0, 0.0], "v": [0.0, -e.m / total * speed]},
        {"preset": "electron", "x": [p.m / total * R0, 0.0], "v": [0.0, p.m / total * speed]},
    ]
    return {
        "scenario": law["id"],
        "universe": {"phi_bar_deg": 79.86, "dimension": 2, "units": "SI"},
        "law": law,
        "bodies": bodies,
        "numerics": {"softening": 0.0, "t_end": PERIODS * period, "record_every": 25},
        "kind": "finding",
        "preregistered": False,
        "producer": producer,
    }


if __name__ == "__main__":
    producer = sys.argv[1] if len(sys.argv) > 1 else PRODUCER
    folders = {}
    for law in ({"id": "L0"}, {"id": "L1a", "lambda": 1.0}):
        result = run(settings(law, producer), out_root=Path("results") / "T1.4")
        folders[law["id"]] = result.folder
        drift = result.summary["conservation"]
        print(
            f"{law['id']}: {result.summary['steps']} steps; L0 energy drift {drift['energy_re']:.3e}, "
            f"momentum drift {drift['momentum']:.3e}; results in {result.folder}"
        )
    for line in make_figures(folders["L0"], folders["L1a"]):
        print(line)
    print("EXPLORATORY demo: L1a is a hypothesis, excluded at lambda = 1 by the neutron (T9.1). Not a result.")
