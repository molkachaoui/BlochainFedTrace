"""Test de bout en bout de la phase 0 : fausses données -> empreintes -> LocalLedger -> certification.

Il valide les contrats partagés. Quand l'AnchoringAgent sera prêt, il remplacera
l'ancrage manuel ci-dessous.
"""
import json

import numpy as np
import pytest

from blockchain.local_ledger import LocalLedger
from common import paths
from common.schemas import ContributionRecord, GlobalModelRecord
from tests.fixtures.make_fake_rounds import CLINICS, POISONED, make_rounds
from traceability.certification import UncertifiedModel, assert_certified
from traceability.hashing import hash_npz, load_npz


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("FEDTRACE_STORAGE", str(tmp_path))
    summary = make_rounds(3)
    return summary, LocalLedger()


def anchor_all(ledger, n_rounds):
    parent = hash_npz(paths.global_model_path(0))
    ledger.register_global_model(GlobalModelRecord(
        round_id=0, model_hash=parent, parent_model_hash=None,
        strategy="init", accepted=[], rejected=[], metrics={}))
    for r in range(1, n_rounds + 1):
        hashes = {}
        for c in CLINICS:                                   # AVANT agrégation
            hashes[c] = hash_npz(paths.update_path(r, c))
            ledger.register_contribution(ContributionRecord(
                round_id=r, clinic_id=c, update_hash=hashes[c], num_samples=100))
        model_hash = hash_npz(paths.global_model_path(r))   # APRÈS agrégation
        ledger.register_global_model(GlobalModelRecord(
            round_id=r, model_hash=model_hash, parent_model_hash=parent,
            strategy="trimmed_mean",
            accepted=[hashes[c] for c in CLINICS if c != POISONED],
            rejected=[hashes[POISONED]],
            metrics=json.loads(paths.metrics_path(r).read_text())))
        parent = model_hash
    return parent


def test_certified_model_accepted(env):
    summary, ledger = env
    anchor_all(ledger, summary["rounds"])
    assert assert_certified(ledger, load_npz(paths.global_model_path(3)))


def test_substituted_model_refused(env):
    summary, ledger = env
    anchor_all(ledger, summary["rounds"])
    fake = {k: v + 1e-4 for k, v in load_npz(paths.global_model_path(3)).items()}
    with pytest.raises(UncertifiedModel):
        assert_certified(ledger, fake)


def test_provenance_back_to_initial_model(env):
    summary, ledger = env
    last = anchor_all(ledger, summary["rounds"])
    chain = ledger.get_model_provenance(last)
    assert [m.round_id for m in chain] == [3, 2, 1, 0]
    assert all(len(m.rejected) == 1 for m in chain[:-1])     # exclusion ancrée
