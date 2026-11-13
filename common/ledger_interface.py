"""Interface abstraite du registre distribué.

Le Membre 2 l'implémente deux fois : LocalLedger (chaîne simplifiée locale)
puis la plateforme retenue (Fabric ou Ethereum). Le Membre 3 ne dépend que
de cette interface : changer de registre ne modifie pas son code.
"""
from abc import ABC, abstractmethod
from typing import Optional

from common.schemas import (ContributionRecord, DiagnosisRecord,
                            GlobalModelRecord, TxReceipt)


class LedgerUnavailable(Exception):
    """Registre indisponible : l'agent d'ancrage doit mettre l'enregistrement en file."""


class DuplicateRecord(Exception):
    """Un enregistrement avec la même clé existe déjà."""


class LedgerService(ABC):
    @abstractmethod
    def register_contribution(self, rec: ContributionRecord) -> TxReceipt: ...

    @abstractmethod
    def register_global_model(self, rec: GlobalModelRecord) -> TxReceipt: ...

    @abstractmethod
    def register_diagnosis(self, rec: DiagnosisRecord) -> TxReceipt: ...

    @abstractmethod
    def verify_model(self, model_hash: str) -> bool:
        """True si l'empreinte correspond à un round certifié."""

    @abstractmethod
    def verify_diagnosis(self, diagnosis_id: str) -> Optional[DiagnosisRecord]:
        """Renvoie l'enregistrement ancré ; la comparaison d'empreinte est faite par le Membre 3."""

    @abstractmethod
    def get_model_provenance(self, model_hash: str) -> list[GlobalModelRecord]:
        """Chaîne des modèles, du modèle demandé jusqu'au modèle initial."""

    @abstractmethod
    def get_history(self, key: str) -> list[dict]:
        """Historique complet d'une clé."""
