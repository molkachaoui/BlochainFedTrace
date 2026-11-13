"""Interface entre la fédération (Membre 1) et l'agent d'ancrage (Membre 3).

La stratégie d'agrégation appelle on_contributions AVANT d'agréger et
on_global_model APRÈS. NoOpHook = configuration « fédération seule ».
"""
from typing import Protocol

import numpy as np

NamedParams = dict[str, np.ndarray]


class AnchoringHook(Protocol):
    def on_contributions(self, round_id: int,
                         updates: dict[str, tuple[NamedParams, int]]) -> None:
        """clinic_id -> (paramètres nommés, nombre d'échantillons). AVANT agrégation."""

    def on_global_model(self, round_id: int, params: NamedParams, strategy: str,
                        accepted: list[str], rejected: list[str],
                        metrics: dict) -> None:
        """APRÈS agrégation. accepted / rejected contiennent des clinic_id."""


class NoOpHook:
    def on_contributions(self, round_id, updates):
        pass

    def on_global_model(self, round_id, params, strategy, accepted, rejected, metrics):
        pass
