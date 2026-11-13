"""Génère de fausses mises à jour pour tester l'ancrage sans la vraie fédération.

3 cliniques x N rounds ; clinic_C envoie une mise à jour aberrante (empoisonnée).
Usage : python -m tests.fixtures.make_fake_rounds --rounds 3
"""
import argparse
import json

import numpy as np

from common import paths
from traceability.hashing import save_npz

CLINICS = ["clinic_A", "clinic_B", "clinic_C"]
POISONED = "clinic_C"
SHAPES = {"fc1.weight": (16, 8), "fc1.bias": (16,), "fc2.weight": (2, 16), "fc2.bias": (2,)}


def make_rounds(n_rounds: int = 3, seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    global_params = {k: rng.normal(size=s) for k, s in SHAPES.items()}
    save_npz(paths.global_model_path(0), global_params)
    summary = {"rounds": n_rounds, "clinics": CLINICS, "poisoned": POISONED}
    for r in range(1, n_rounds + 1):
        updates = {}
        for c in CLINICS:
            scale = 50.0 if c == POISONED else 0.1
            upd = {k: v + rng.normal(scale=scale, size=v.shape) for k, v in global_params.items()}
            save_npz(paths.update_path(r, c), upd)
            updates[c] = upd
        honest = [updates[c] for c in CLINICS if c != POISONED]
        global_params = {k: np.mean([u[k] for u in honest], axis=0) for k in SHAPES}
        save_npz(paths.global_model_path(r), global_params)
        paths.metrics_path(r).write_text(json.dumps({"accuracy": 0.70 + 0.05 * r}))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    print(make_rounds(ap.parse_args().rounds))
