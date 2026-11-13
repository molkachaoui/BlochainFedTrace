# FedTrace

Ancrage et vérification de la provenance d'un apprentissage fédéré pour le
diagnostic des maladies auto-immunes. Prototype pédagogique — **aucune donnée
de patient réel**.

## Démarrage (Windows, PowerShell)

```powershell
cd C:\Users\DELL\OneDrive\Bureau\BlockChain
.\setup.ps1                              # dépendances communes
.\setup.ps1 -Module federated_learning   # Membre 1
.\setup.ps1 -Module blockchain           # Membre 2
.\setup.ps1 -Module traceability         # Membre 3
pytest                                   # 14 tests doivent passer
```

Si PowerShell bloque le script : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Organisation

| Dossier | Responsable | Rôle |
|---|---|---|
| `common/` | **les 3** | contrats partagés : formats, interface du registre, hook FL, stockage |
| `federated_learning/` | Membre 1 | fédération, stratégies d'agrégation, empoisonnement |
| `blockchain/` | Membre 2 | `LocalLedger` (doublure), plateforme réelle, contrat |
| `traceability/` | Membre 3 | empreintes, pseudonymisation, agent d'ancrage, certification, provenance |
| `backend/`, `frontend/` | Membre 3 | API et interface d'audit |
| `tests/` | tous | données factices et tests d'intégration |
| `storage/` | — | stockage hors chaîne (ignoré par git) |

## Comment chacun travaille sans attendre les autres

- **Membre 1** utilise `common.hooks.NoOpHook` → fédération seule.
- **Membre 2** implémente `common.ledger_interface.LedgerService`.
- **Membre 3** utilise `LocalLedger` + `tests/fixtures/make_fake_rounds.py`.
- Tout le monde obtient le registre via `blockchain.factory.get_ledger()`
  (`FEDTRACE_LEDGER=local` par défaut, `real` une fois la plateforme prête).

Voir `docs/decisions.md` et `CONTRIBUTING.md`.
