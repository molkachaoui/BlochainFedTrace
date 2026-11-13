# Journal des décisions

| ID | Décision | Statut |
|---|---|---|
| D1 | Python 3.11, venv, pytest ; dépendances par module | adoptée |
| D2 | Règle canonique d'empreinte (ci-dessous) | adoptée — figée |
| D3 | Paramètres toujours en dict nommé, sauvegardés en `.npz` | adoptée |
| D4 | Stockage hors chaîne selon `common/paths.py` | adoptée |
| D5 | Plateforme blockchain : Hyperledger Fabric ou Ethereum | **à instruire (Membre 2)** |
| D6 | Jeu de données médical | **à instruire (Membre 1)** |
| D7 | Stratégie d'agrégation robuste (trimmed mean, Krum, médiane…) | **à instruire (Membre 1)** |

## D2 — Règle canonique d'empreinte
- Paramètres : dict de tableaux nommés ; noms triés alphabétiquement ;
  chaque tableau converti en float32 little-endian contigu ;
  pour chacun : SHA-256 sur nom, `\0`, forme, `\0`, octets bruts.
- JSON (explications) : clés triées, sans espaces (`separators=(",", ":")`), UTF-8.
- Implémentation de référence : `traceability/hashing.py`.

## D3 — Conséquence pour Flower
Flower transmet une liste ordonnée de tableaux. Le Membre 1 la reconvertit
en dict avec les noms du `state_dict` PyTorch (ordre fixe) avant toute
sauvegarde ou appel au hook.

## D5 — Critères de choix du registre (section 7)
Permissionné ou public ; gestion des identités ; règles de validation ;
coût et débit par round ; lecture de l'historique d'une clé ; effort
d'installation. Fabric offre nativement identités fortes et `GetHistoryForKey`
mais s'installe lourdement ; Ethereum + Hardhat est léger mais l'historique
doit être reconstruit depuis les événements. Grâce à `LedgerService`, ce choix
ne modifie le code d'aucun autre module.
