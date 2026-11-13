"""File de reprise persistante des ancrages en échec (Membre 3).

TODO : enregistrer en JSONL (common.paths.retry_queue_path()) chaque
ancrage ayant levé LedgerUnavailable, et les rejouer dans l'ordre au redémarrage.
"""


class RetryQueue:
    def push(self, kind: str, record: dict) -> None:
        raise NotImplementedError

    def replay(self, ledger) -> int:
        """Rejoue la file ; renvoie le nombre d'ancrages réussis."""
        raise NotImplementedError
