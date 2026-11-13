import pytest

from blockchain.local_ledger import LocalLedger
from common.ledger_interface import DuplicateRecord, LedgerUnavailable
from common.schemas import ContributionRecord, GlobalModelRecord


@pytest.fixture
def ledger(tmp_path):
    return LocalLedger(tmp_path / "ledger.jsonl")


def model(h, parent, r):
    return GlobalModelRecord(round_id=r, model_hash=h, parent_model_hash=parent,
                             strategy="fedavg", accepted=[], rejected=[], metrics={})


def test_register_and_verify_model(ledger):
    ledger.register_global_model(model("m0", None, 0))
    assert ledger.verify_model("m0")
    assert not ledger.verify_model("inconnu")


def test_duplicate_rejected(ledger):
    rec = ContributionRecord(round_id=1, clinic_id="clinic_A", update_hash="u1", num_samples=10)
    ledger.register_contribution(rec)
    with pytest.raises(DuplicateRecord):
        ledger.register_contribution(rec)


def test_provenance_chain(ledger):
    ledger.register_global_model(model("m0", None, 0))
    ledger.register_global_model(model("m1", "m0", 1))
    ledger.register_global_model(model("m2", "m1", 2))
    assert [m.model_hash for m in ledger.get_model_provenance("m2")] == ["m2", "m1", "m0"]


def test_offline_raises(ledger):
    ledger.online = False
    with pytest.raises(LedgerUnavailable):
        ledger.register_global_model(model("m0", None, 0))


def test_tampering_breaks_chain(ledger):
    ledger.register_global_model(model("m0", None, 0))
    ledger.register_global_model(model("m1", "m0", 1))
    assert ledger.verify_chain()
    text = ledger.path.read_text().replace('"fedavg"', '"krum"', 1)
    ledger.path.write_text(text)
    assert not ledger.verify_chain()
