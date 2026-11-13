"""Agent d'ancrage (Membre 3) — implémente common.hooks.AnchoringHook.

TODO :
- on_contributions : sauvegarder chaque mise à jour (.npz), la hacher,
  ancrer un ContributionRecord AVANT l'agrégation ;
- on_global_model : hacher le modèle global, convertir accepted/rejected
  (clinic_id -> update_hash), ancrer un GlobalModelRecord avec le parent ;
- en cas de LedgerUnavailable : mettre en RetryQueue ;
- conserver les tx_id pour l'interface d'audit.
"""
from common.ledger_interface import LedgerService


class AnchoringAgent:
    def __init__(self, ledger: LedgerService):
        self.ledger = ledger

    def on_contributions(self, round_id, updates):
        raise NotImplementedError

    def on_global_model(self, round_id, params, strategy, accepted, rejected, metrics):
        raise NotImplementedError
