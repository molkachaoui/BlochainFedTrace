"""Empreintes déterministes — règle canonique figée (voir docs/decisions.md, D2).

Ne pas modifier sans accord des 3 membres : toute modification invalide
toutes les empreintes déjà ancrées.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

NamedParams = dict[str, np.ndarray]


def hash_parameters(params: NamedParams) -> str:
    """SHA-256 d'un ensemble de paramètres nommés.

    Noms triés ; chaque tableau converti en float32 little-endian contigu ;
    on hache le nom, la forme, puis les octets bruts.
    """
    h = hashlib.sha256()
    for name in sorted(params):
        arr = np.ascontiguousarray(params[name], dtype="<f4")
        h.update(name.encode("utf-8")); h.update(b"\x00")
        h.update(str(arr.shape).encode("utf-8")); h.update(b"\x00")
        h.update(arr.tobytes())
    return h.hexdigest()


def hash_json(obj: dict) -> str:
    """SHA-256 d'un objet JSON (explications, comptes rendus)."""
    canon = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


def load_npz(path: str | Path) -> NamedParams:
    with np.load(path) as data:
        return {k: data[k] for k in data.files}


def save_npz(path: str | Path, params: NamedParams) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **params)


def hash_npz(path: str | Path) -> str:
    return hash_parameters(load_npz(path))
