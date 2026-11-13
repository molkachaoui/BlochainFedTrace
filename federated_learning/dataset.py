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

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

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
                low, high = _BOUNDS[feature]
                # Pas de valeur impossible (CRP négative, âge > 90…).
                X[rows, col] = np.clip(rng.normal(mean, std, rows.size), low, high)
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
    indices = partition_indices(y, clinics=clinics, mode=mode, alpha=alpha, seed=seed)
    return {clinic: (X[idx], y[idx]) for clinic, idx in indices.items()}


def partition_indices(
    y: np.ndarray,
    clinics: list[str] | None = None,
    mode: str = "iid",
    alpha: float = 0.5,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Indices (triés) des patients attribués à chaque clinique.

    Même règle que `partition`, qui s'appuie sur cette fonction.
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
    return {c: np.sort(np.concatenate(assigned[c])) for c in clinics}


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


def _write_csv(path: Path, header: list[str], rows) -> None:
    """Écrit un fichier CSV (séparateur virgule, UTF-8)."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def _fmt(value: float) -> str:
    """Nombre lisible ; cellule vide pour une valeur manquante."""
    return "" if np.isnan(value) else f"{value:.4g}"


def export_dataset(
    out_dir: str | Path = "data",
    n_patients: int = 3000,
    seed: int = 42,
    mode: str = "iid",
    alpha: float = 0.5,
    test_ratio: float = 0.2,
) -> list[Path]:
    """Écrit le jeu en CSV pour pouvoir le consulter (Excel, pandas…).

    - patients.csv : patients bruts (valeurs manquantes = cellule vide),
      classe en clair et clinique de chaque patient ;
    - clinic_X.csv : données nettoyées de la clinique, avec la colonne
      `split` (train / test) identique à `load_clinic_datasets`.
    Retourne la liste des fichiers écrits.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    X_raw, y = generate_synthetic(n_patients=n_patients, seed=seed)
    X_clean = clean(X_raw)
    indices = partition_indices(y, mode=mode, alpha=alpha, seed=seed)

    clinic_of = np.empty(len(y), dtype=object)
    for clinic, idx in indices.items():
        clinic_of[idx] = clinic
    files = [out / "patients.csv"]
    _write_csv(
        files[0],
        ["patient_id", "clinique", *FEATURES, "classe"],
        (
            [f"P{i:05d}", clinic_of[i], *(_fmt(v) for v in X_raw[i]), CLASSES[y[i]]]
            for i in range(len(y))
        ),
    )

    for clinic, idx in indices.items():
        order = np.random.default_rng(seed).permutation(len(idx))
        n_test = int(round(len(idx) * test_ratio))
        split = np.full(len(idx), "train", dtype=object)
        split[order[:n_test]] = "test"
        path = out / f"{clinic}.csv"
        _write_csv(
            path,
            ["patient_id", *FEATURES, "classe", "split"],
            (
                [f"P{i:05d}", *(f"{v:.4f}" for v in X_clean[i]), CLASSES[y[i]], s]
                for i, s in zip(idx, split)
            ),
        )
        files.append(path)
    return files


def main(argv: list[str] | None = None) -> None:
    """Commande : python -m federated_learning.dataset [--mode non_iid] ..."""
    parser = argparse.ArgumentParser(description="Exporte le jeu synthétique en CSV.")
    parser.add_argument("--out", default="data")
    parser.add_argument("--n-patients", type=int, default=3000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mode", choices=["iid", "non_iid"], default="iid")
    parser.add_argument("--alpha", type=float, default=0.5)
    args = parser.parse_args(argv)
    for path in export_dataset(args.out, args.n_patients, args.seed, args.mode, args.alpha):
        print(f"-> {path}")


if __name__ == "__main__":
    main()
