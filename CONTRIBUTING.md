# Règles de travail

## Git
- `main` est protégée : aucun push direct.
- Une branche par tâche : `feat/fl-fedavg`, `feat/bc-local-ledger`, `feat/tr-retry-queue`, `fix/...`
- Préfixes : `fl` (Membre 1), `bc` (Membre 2), `tr` (Membre 3), `common`, `docs`.
- Fusion par Pull Request, relue par au moins un autre membre ; `pytest` doit passer.

## Le dossier `common/`
Contrat entre les trois modules. Toute modification :
1. est proposée dans une PR dédiée `common/...` ;
2. est approuvée par **les trois** membres ;
3. est notée dans `docs/decisions.md`.

Il en va de même pour `traceability/hashing.py` (règle canonique D2).

## Code
- Python 3.11, une fonction = une responsabilité, docstrings en français.
- Chaque module livre ses tests dans son dossier `tests/`.
