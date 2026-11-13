import numpy as np

from traceability.hashing import hash_json, hash_parameters


def params(seed=0):
    rng = np.random.default_rng(seed)
    return {"fc1.weight": rng.normal(size=(4, 3)), "fc1.bias": rng.normal(size=4)}


def test_reproducible():
    assert hash_parameters(params()) == hash_parameters(params())


def test_order_independent():
    p = params()
    assert hash_parameters(p) == hash_parameters(dict(reversed(list(p.items()))))


def test_dtype_normalized():
    p = params()
    p32 = {k: v.astype(np.float32) for k, v in p.items()}
    assert hash_parameters(p) == hash_parameters(p32)


def test_single_change_detected():
    p = params()
    q = {k: v.copy() for k, v in p.items()}
    q["fc1.bias"][0] += 1e-3
    assert hash_parameters(p) != hash_parameters(q)


def test_shape_matters():
    a = {"w": np.zeros(6)}
    b = {"w": np.zeros((2, 3))}
    assert hash_parameters(a) != hash_parameters(b)


def test_json_key_order_independent_and_tamper_detected():
    e = {"facteurs": ["ANA+", "CRP"], "score": 0.91}
    assert hash_json(e) == hash_json({"score": 0.91, "facteurs": ["ANA+", "CRP"]})
    assert hash_json(e) != hash_json({"score": 0.91, "facteurs": ["CRP"]})
