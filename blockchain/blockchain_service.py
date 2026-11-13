"""Implémentation de LedgerService sur la plateforme retenue (Membre 2).

TODO Membre 2 : après l'étude comparative (docs/decisions.md), implémenter
cette classe (Fabric via SDK/gateway, ou Ethereum via Web3.py).
"""
from common.ledger_interface import LedgerService


class BlockchainService(LedgerService):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError("Plateforme non encore choisie — utiliser LocalLedger")
