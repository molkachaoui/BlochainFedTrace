"""Porte de certification (Membre 3)."""
from common.ledger_interface import LedgerService
from traceability.hashing import NamedParams, hash_parameters


class UncertifiedModel(Exception):
    """Le modèle chargé ne correspond à aucun round ancré : diagnostic refusé."""


def assert_certified(ledger: LedgerService, params: NamedParams) -> str:
    """Renvoie l'empreinte du modèle s'il est certifié, sinon lève UncertifiedModel."""
    model_hash = hash_parameters(params)
    if not ledger.verify_model(model_hash):
        raise UncertifiedModel(model_hash)
    return model_hash
