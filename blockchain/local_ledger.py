"""Registre local simplifié : chaîne de blocs chaînés par empreinte, sans infrastructure.

Sert de doublure pendant que la plateforme réelle est installée (section 7).
Passer `online = False` simule une indisponibilité (scénario 5).
"""
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional

from common import paths
from common.ledger_interface import DuplicateRecord, LedgerService, LedgerUnavailable
from common.schemas import (ContributionRecord, DiagnosisRecord,
                            GlobalModelRecord, TxReceipt)


def _block_hash(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class LocalLedger(LedgerService):
    def __init__(self, path: Optional[str | Path] = None):
        self.path = Path(path) if path else paths.ledger_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self.online = True

    # ---- interne ----
    def _blocks(self) -> list[dict]:
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def _check_online(self):
        if not self.online:
            raise LedgerUnavailable("registre local hors ligne")

    def _append(self, kind: str, key: str, payload: dict) -> TxReceipt:
        self._check_online()
        blocks = self._blocks()
        if any(b["kind"] == kind and b["key"] == key for b in blocks):
            raise DuplicateRecord(f"{kind} déjà ancré : {key}")
        body = {
            "index": len(blocks),
            "kind": kind,
            "key": key,
            "payload": payload,
            "prev_hash": blocks[-1]["block_hash"] if blocks else "0" * 64,
            "tx_id": uuid.uuid4().hex,
        }
        body["block_hash"] = _block_hash(body)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(body) + "\n")
        return TxReceipt(tx_id=body["tx_id"], record_key=key)

    def verify_chain(self) -> bool:
        """Vérifie qu'aucun bloc n'a été modifié dans le fichier."""
        prev = "0" * 64
        for b in self._blocks():
            body = {k: v for k, v in b.items() if k != "block_hash"}
            if b["prev_hash"] != prev or _block_hash(body) != b["block_hash"]:
                return False
            prev = b["block_hash"]
        return True

    # ---- écritures ----
    def register_contribution(self, rec: ContributionRecord) -> TxReceipt:
        return self._append("contribution", rec.update_hash, rec.model_dump(mode="json"))

    def register_global_model(self, rec: GlobalModelRecord) -> TxReceipt:
        return self._append("model", rec.model_hash, rec.model_dump(mode="json"))

    def register_diagnosis(self, rec: DiagnosisRecord) -> TxReceipt:
        return self._append("diagnosis", rec.diagnosis_id, rec.model_dump(mode="json"))

    # ---- lectures ----
    def verify_model(self, model_hash: str) -> bool:
        self._check_online()
        return any(b["kind"] == "model" and b["key"] == model_hash for b in self._blocks())

    def verify_diagnosis(self, diagnosis_id: str) -> Optional[DiagnosisRecord]:
        self._check_online()
        for b in self._blocks():
            if b["kind"] == "diagnosis" and b["key"] == diagnosis_id:
                return DiagnosisRecord(**b["payload"])
        return None

    def get_model_provenance(self, model_hash: str) -> list[GlobalModelRecord]:
        self._check_online()
        models = {b["key"]: GlobalModelRecord(**b["payload"])
                  for b in self._blocks() if b["kind"] == "model"}
        chain, current = [], model_hash
        while current and current in models:
            chain.append(models[current])
            current = models[current].parent_model_hash
        return chain

    def get_history(self, key: str) -> list[dict]:
        self._check_online()
        return [b for b in self._blocks() if b["key"] == key]
