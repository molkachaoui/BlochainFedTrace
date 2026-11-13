"""Organisation du stockage hors chaîne (poids, métriques, explications).

La racine peut être changée avec la variable d'environnement FEDTRACE_STORAGE.
"""
import os
from pathlib import Path


def root() -> Path:
    return Path(os.environ.get("FEDTRACE_STORAGE", "storage"))


def round_dir(round_id: int) -> Path:
    return root() / "rounds" / f"r{round_id:03d}"


def update_path(round_id: int, clinic_id: str) -> Path:
    return round_dir(round_id) / f"{clinic_id}_update.npz"


def global_model_path(round_id: int) -> Path:
    return round_dir(round_id) / "global_model.npz"


def metrics_path(round_id: int) -> Path:
    return round_dir(round_id) / "metrics.json"


def explanation_path(diagnosis_id: str) -> Path:
    return root() / "diagnoses" / diagnosis_id / "explanation.json"


def ledger_path() -> Path:
    return root() / "local_ledger.jsonl"


def retry_queue_path() -> Path:
    return root() / "retry_queue.jsonl"
