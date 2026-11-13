"""Chargement, nettoyage et partition du jeu de données en 3 cliniques.

Décision D6 : jeu **synthétique** généré ici, avec une graine fixe.
Aucune donnée de patient réel n'est utilisée.

Chaque patient fictif a 10 variables cliniques (âge, sexe et biomarqueurs)
et une classe parmi : sain, lupus, polyarthrite rhumatoïde. Les distributions
s'inspirent des profils typiques de ces maladies (ANA et anti-dsDNA élevés,
C3/C4 bas pour le lupus ; FR et anti-CCP élevés pour la PR) et se recouvrent
volontairement pour que la tâche ne soit pas triviale.

Utilisation type :
    data = load_clinic_datasets(seed=42, mode="non_iid")
    X_train, y_train = data["clinic_A"].X_train, data["clinic_A"].y_train

Règle : les paramètres du modèle sont toujours manipulés en dict nommé
(state_dict) et sauvegardés en .npz selon common.paths — voir
docs/decisions.md (D2, D3).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

CLINICS = ["clinic_A", "clinic_B", "clinic_C"]
CLASSES = ["sain", "lupus", "polyarthrite_rhumatoide"]

# Variables, dans l'ordre des colonnes de X.
FEATURES = [
    "age",                 # années
    "sexe_femme",          # 1 = femme, 0 = homme
    "ana_titre",           # log2 du titre d'anticorps antinucléaires
    "anti_dsdna",          # UI/mL
    "facteur_rhumatoide",  # UI/mL
    "anti_ccp",            # U/mL
    "crp",                 # mg/L
    "vs",                  # vitesse de sédimentation, mm/h
    "c3",                  # g/L
    "c4",                  # g/L
]

# Bornes physiologiques plausibles (clip) et valeur de référence normale
# utilisée pour remplacer une valeur manquante. Fixes, donc identiques
# dans toutes les cliniques : aucune information ne circule entre elles.
_BOUNDS = {
    "age": (18.0, 90.0),
    "sexe_femme": (0.0, 1.0),
    "ana_titre": (0.0, 12.0),
    "anti_dsdna": (0.0, 400.0),
    "facteur_rhumatoide": (0.0, 500.0),
    "anti_ccp": (0.0, 500.0),
    "crp": (0.0, 200.0),
    "vs": (0.0, 140.0),
    "c3": (0.2, 2.5),
    "c4": (0.02, 0.8),
}
_NORMAL = {
    "age": 45.0, "sexe_femme": 0.5, "ana_titre": 3.0, "anti_dsdna": 5.0,
    "facteur_rhumatoide": 8.0, "anti_ccp": 5.0, "crp": 3.0, "vs": 12.0,
    "c3": 1.2, "c4": 0.25,
}

# Paramètres de génération par classe : (moyenne, écart-type) d'une loi
# normale, sauf sexe_femme (probabilité d'être une femme).
_PROFILES = {
    "sain": {
        "age": (45, 15), "sexe_femme": 0.5, "ana_titre": (3.0, 1.2),
        "anti_dsdna": (5, 4), "facteur_rhumatoide": (8, 6),
        "anti_ccp": (5, 4), "crp": (3, 2.5), "vs": (12, 7),
        "c3": (1.2, 0.2), "c4": (0.25, 0.07),
    },
    "lupus": {
        "age": (35, 11), "sexe_femme": 0.9, "ana_titre": (7.5, 1.5),
        "anti_dsdna": (90, 60), "facteur_rhumatoide": (15, 15),
        "anti_ccp": (8, 8), "crp": (10, 9), "vs": (40, 18),
        "c3": (0.75, 0.22), "c4": (0.12, 0.06),
    },
    "polyarthrite_rhumatoide": {
        "age": (55, 12), "sexe_femme": 0.75, "ana_titre": (4.5, 1.8),
        "anti_dsdna": (8, 8), "facteur_rhumatoide": (80, 60),
        "anti_ccp": (110, 80), "crp": (22, 15), "vs": (35, 15),
        "c3": (1.3, 0.25), "c4": (0.3, 0.08),
    },
}


@dataclass
class ClinicData:
    """Données d'une clinique, déjà nettoyées et séparées entraînement/test."""

    clinic_id: str
    X_train: np.ndarray
    y_train: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray


def generate_synthetic(
    n_patients: int = 3000,
    seed: int = 42,
    missing_rate: float = 0.02,
    class_weights: tuple[float, float, float] = (0.5, 0.25, 0.25),
) -> tuple[np.ndarray, np.ndarray]:
    """Génère des patients fictifs bruts (avec valeurs manquantes).

    Retourne X (n_patients, 10) en float32, pouvant contenir des NaN,
    et y (n_patients,) en int64, indices dans CLASSES.
    """
    rng = np.random.default_rng(seed)
    y = rng.choice(len(CLASSES), size=n_patients, p=np.asarray(class_weights))
    X = np.empty((n_patients, len(FEATURES)), dtype=np.float64)
    for class_idx, class_name in enumerate(CLASSES):
        rows = np.flatnonzero(y == class_idx)
        profile = _PROFILES[class_name]
        for col, feature in enumerate(FEATURES):
            spec = profile[feature]
            if feature == "sexe_femme":
                X[rows, col] = rng.random(rows.size) < spec
            else:
                mean, std = spec
                X[rows, col] = rng.normal(mean, std, rows.size)
    # Valeurs manquantes aléatoires, comme dans un vrai dossier clinique.
    X[rng.random(X.shape) < missing_rate] = np.nan
    return X.astype(np.float32), y.astype(np.int64)


def clean(X: np.ndarray) -> np.ndarray:
    """Nettoie X : remplace les NaN par la valeur normale, borne, normalise.

    La normalisation utilise des constantes fixes (pas de statistiques
    calculées sur les données), elle est donc identique dans chaque clinique.
    """
    X = np.array(X, dtype=np.float32, copy=True)
    for col, feature in enumerate(FEATURES):
        column = X[:, col]
        column[np.isnan(column)] = _NORMAL[feature]
        low, high = _BOUNDS[feature]
        np.clip(column, low, high, out=column)
        X[:, col] = (column - low) / (high - low)  # ramené dans [0, 1]
    return X


def partition(
    X: np.ndarray,
    y: np.ndarray,
    clinics: list[str] | None = None,
    mode: str = "iid",
    alpha: float = 0.5,
    seed: int = 42,
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Répartit les patients entre les cliniques, sans recouvrement.

    mode="iid"     : tirage uniforme, chaque clinique a la même répartition
                     des classes en moyenne.
    mode="non_iid" : pour chaque classe, les proportions par clinique suivent
                     une loi de Dirichlet(alpha) ; plus alpha est petit, plus
                     les cliniques sont différentes.
    """
    clinics = list(clinics or CLINICS)
    rng = np.random.default_rng(seed)
    assigned: dict[str, list[np.ndarray]] = {c: [] for c in clinics}
    if mode == "iid":
        order = rng.permutation(len(y))
        for clinic, idx in zip(clinics, np.array_split(order, len(clinics))):
            assigned[clinic].append(idx)
    elif mode == "non_iid":
        for class_idx in np.unique(y):
            idx = rng.permutation(np.flatnonzero(y == class_idx))
            shares = rng.dirichlet([alpha] * len(clinics))
            cuts = (np.cumsum(shares)[:-1] * idx.size).astype(int)
            for clinic, part in zip(clinics, np.split(idx, cuts)):
                assigned[clinic].append(part)
    else:
        raise ValueError(f"mode inconnu : {mode!r} (attendu 'iid' ou 'non_iid')")
    result = {}
    for clinic in clinics:
        idx = np.sort(np.concatenate(assigned[clinic]))
        result[clinic] = (X[idx], y[idx])
    return result


def train_test_split(
    X: np.ndarray, y: np.ndarray, test_ratio: float = 0.2, seed: int = 42
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Sépare les données d'une clinique en entraînement et test."""
    order = np.random.default_rng(seed).permutation(len(y))
    n_test = int(round(len(y) * test_ratio))
    test, train = order[:n_test], order[n_test:]
    return X[train], y[train], X[test], y[test]


def load_clinic_datasets(
    n_patients: int = 3000,
    seed: int = 42,
    mode: str = "iid",
    alpha: float = 0.5,
    test_ratio: float = 0.2,
) -> dict[str, ClinicData]:
    """Point d'entrée : génère, nettoie et partitionne en 3 cliniques."""
    X, y = generate_synthetic(n_patients=n_patients, seed=seed)
    X = clean(X)
    parts = partition(X, y, mode=mode, alpha=alpha, seed=seed)
    return {
        clinic: ClinicData(clinic, *train_test_split(Xc, yc, test_ratio, seed))
        for clinic, (Xc, yc) in parts.items()
    }
