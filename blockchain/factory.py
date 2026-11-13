"""Point d'entrée unique : les autres modules appellent get_ledger(), jamais une classe directement.

FEDTRACE_LEDGER=local (défaut) | real
"""
import os

from common.ledger_interface import LedgerService


def get_ledger() -> LedgerService:
    mode = os.environ.get("FEDTRACE_LEDGER", "local")
    if mode == "local":
        from blockchain.local_ledger import LocalLedger
        return LocalLedger()
    if mode == "real":
        from blockchain.blockchain_service import BlockchainService
        return BlockchainService()
    raise ValueError(f"FEDTRACE_LEDGER inconnu : {mode}")
