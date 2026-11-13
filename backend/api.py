"""API FastAPI (Membre 3).

Lancer : uvicorn backend.api:app --reload
"""
from fastapi import FastAPI

from blockchain.factory import get_ledger

app = FastAPI(title="FedTrace")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/models/{model_hash}/verify")
def verify_model(model_hash: str):
    return {"model_hash": model_hash, "certified": get_ledger().verify_model(model_hash)}


@app.get("/models/{model_hash}/provenance")
def provenance(model_hash: str):
    return [m.model_dump(mode="json") for m in get_ledger().get_model_provenance(model_hash)]
