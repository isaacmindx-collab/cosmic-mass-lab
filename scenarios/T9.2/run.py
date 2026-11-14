"""T9.2: Hydrogen under the charge share (L5c): binding energy 5.71 eV (book, Chapter 9), against 13.598 eV.

Setup and pass criterion: docs/05-scenarios-and-tests.md, section 2, T9. Pre-registration:
team/notes/T9.2.md. L1a is a hypothesis (decision D1); this is a measurement check (decision D4).
The binding energy uses the book's scaling (the square of the pull) with the pull from the engine.

    python scenarios/T9.2/run.py        # writes results/T9.2/<run-id>/
"""

import sys

from cosmicmass.gates.t0 import write_gate_result
from cosmicmass.gates.t9 import t9_2

PRODUCER = "Claude Opus 5.5 in OpenCode, local (sponsor @MostafaDerraz)"

if __name__ == "__main__":
    outcome = t9_2()
    folder = write_gate_result(outcome, producer=sys.argv[1] if len(sys.argv) > 1 else PRODUCER,
                               kind="measurement-check", law="the hypothesis L1a (charge share only, L5c)")
    for name, case in outcome["cases"].items():
        print(f"{'pass' if case['pass'] else 'FAIL'}  T9.2 {name}")
    binding = outcome["cases"]["binding"]
    print(f"binding energy {binding['binding_energy_eV']:.4f} eV (book 5.71, measured 13.598)")
    print(f"T9.2: {'pass' if outcome['pass'] else 'FAIL'}; results in {folder}")
    sys.exit(0 if outcome["pass"] else 1)
