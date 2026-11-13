"""Formats des enregistrements ancrés (section 4 du cahier des charges).

Aucune donnée patient ni aucun poids de modèle ici : uniquement des empreintes
et des métadonnées.
"""
from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class ContributionRecord(BaseModel):
    """Ancré APRÈS l'entraînement local, AVANT l'agrégation."""
    round_id: int
    clinic_id: str                                        # ex. "clinic_A"
    update_hash: str                                      # SHA-256 hex de la mise à jour
    num_samples: int                                      # volume déclaré
    privacy_params: dict = Field(default_factory=dict)    # ex. {"dp": False}
    timestamp: datetime = Field(default_factory=now_utc)


class GlobalModelRecord(BaseModel):
    """Ancré APRÈS l'agrégation du round n."""
    round_id: int
    model_hash: str
    parent_model_hash: Optional[str]      # None pour le modèle initial
    strategy: str                         # "fedavg" | "trimmed_mean" | "krum" | "init"
    accepted: list[str]                   # update_hash des contributions retenues
    rejected: list[str]                   # update_hash des contributions écartées
    metrics: dict                         # ex. {"accuracy": 0.87, "f1": 0.82}
    timestamp: datetime = Field(default_factory=now_utc)


class DiagnosisRecord(BaseModel):
    """Ancré à chaque diagnostic."""
    diagnosis_id: str
    model_hash: str
    explanation_hash: str
    clinic_id: str
    case_pseudonym: str                   # jamais une identité réelle
    probability: float
    validation_status: Literal["pending", "validated", "rejected"] = "pending"
    timestamp: datetime = Field(default_factory=now_utc)


class TxReceipt(BaseModel):
    tx_id: str
    record_key: str
    timestamp: datetime = Field(default_factory=now_utc)
