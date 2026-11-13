"""Tests du jeu de données synthétique (D6)."""
import numpy as np
import pytest

from federated_learning import dataset as ds


def test_generation_forme_et_types():
    X, y = ds.generate_synthetic(n_patients=500, seed=1)
    assert X.shape == (500, len(ds.FEATURES))
    assert X.dtype == np.float32 and y.dtype == np.int64
    assert set(np.unique(y)) <= set(range(len(ds.CLASSES)))


def test_generation_reproductible():
    X1, y1 = ds.generate_synthetic(n_patients=300, seed=7)
    X2, y2 = ds.generate_synthetic(n_patients=300, seed=7)
    np.testing.assert_array_equal(X1, X2)
    np.testing.assert_array_equal(y1, y2)
    X3, _ = ds.generate_synthetic(n_patients=300, seed=8)
    assert not np.array_equal(np.nan_to_num(X1), np.nan_to_num(X3))


def test_profils_cliniques_coherents():
    X, y = ds.generate_synthetic(n_patients=3000, seed=0, missing_rate=0.0)
    col = {f: i for i, f in enumerate(ds.FEATURES)}
    sain, lupus, pr = (X[y == k] for k in range(3))
    assert lupus[:, col["anti_dsdna"]].mean() > sain[:, col["anti_dsdna"]].mean()
    assert lupus[:, col["c3"]].mean() < sain[:, col["c3"]].mean()
    assert pr[:, col["anti_ccp"]].mean() > lupus[:, col["anti_ccp"]].mean()


def test_nettoyage_sans_nan_et_dans_0_1():
    X, _ = ds.generate_synthetic(n_patients=500, seed=2, missing_rate=0.1)
    assert np.isnan(X).any()
    Xc = ds.clean(X)
    assert not np.isnan(Xc).any()
    assert Xc.min() >= 0.0 and Xc.max() <= 1.0
    assert np.isnan(X).any(), "clean ne doit pas modifier l'entrée"


@pytest.mark.parametrize("mode", ["iid", "non_iid"])
def test_partition_disjointe_et_complete(mode):
    X, y = ds.generate_synthetic(n_patients=900, seed=3)
    ids = np.arange(len(y), dtype=np.float32)[:, None]
    parts = ds.partition(ids, y, mode=mode, seed=3)
    assert list(parts) == ds.CLINICS
    all_ids = np.concatenate([p[0].ravel() for p in parts.values()])
    assert len(all_ids) == len(y)
    assert len(np.unique(all_ids)) == len(y)


def test_non_iid_plus_heterogene_que_iid():
    X, y = ds.generate_synthetic(n_patients=3000, seed=4)

    def ecart(parts):
        props = np.array([np.bincount(yc, minlength=3) / len(yc) for _, yc in parts.values()])
        return props.std(axis=0).sum()

    assert ecart(ds.partition(X, y, mode="non_iid", alpha=0.3, seed=4)) > ecart(
        ds.partition(X, y, mode="iid", seed=4)
    )


def test_mode_inconnu():
    X, y = ds.generate_synthetic(n_patients=50, seed=5)
    with pytest.raises(ValueError):
        ds.partition(X, y, mode="autre")


def test_load_clinic_datasets():
    data = ds.load_clinic_datasets(n_patients=1000, seed=6, mode="non_iid")
    assert list(data) == ds.CLINICS
    total = 0
    for clinic, d in data.items():
        assert d.clinic_id == clinic
        assert len(d.X_train) == len(d.y_train) and len(d.X_test) == len(d.y_test)
        assert not np.isnan(d.X_train).any()
        total += len(d.y_train) + len(d.y_test)
    assert total == 1000
