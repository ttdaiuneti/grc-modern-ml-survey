"""E1 datasets: load + z-score standardize. Capped at n<=600 for PH feasibility.

Each dataset returns (X_standardized, y, name). Standardization = z-score (mean 0,
std 1 per feature), matching eval_harness expectation that distances are meaningful.
Saved to standardized/v1/<slug>.csv for reuse (artifact, not live import).
"""
import os
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import (
    load_iris, load_wine, load_breast_cancer,
)

STD_DIR = os.path.join(os.path.dirname(__file__), "standardized", "v1")
os.makedirs(STD_DIR, exist_ok=True)


def _openml(name, version=1):
    from sklearn.datasets import fetch_openml
    d = fetch_openml(name, version=version, as_frame=False, parser="auto")
    X = np.asarray(d.data, dtype=float)
    y = pd.factorize(d.target)[0]
    return X, y


def _loaders():
    return {
        "iris":       lambda: (load_iris().data, load_iris().target),
        "wine":       lambda: (load_wine().data, load_wine().target),
        "wdbc":       lambda: (load_breast_cancer().data, load_breast_cancer().target),
        "ionosphere": lambda: _openml("ionosphere", 1),
        "sonar":      lambda: _openml("sonar", 1),
        "seeds":      lambda: _openml("seeds", 1),
        "glass":      lambda: _openml("glass", 1),
        "ecoli":      lambda: _openml("ecoli", 1),
        "parkinsons": lambda: _openml("parkinsons", 1),
        "heart":      lambda: _openml("heart-statlog", 1),
    }


def load_all(cap_n=600, verbose=True):
    """Load, standardize, cap n. Returns list of (name, X, y)."""
    out = []
    for name, loader in _loaders().items():
        try:
            X, y = loader()
        except Exception as e:
            if verbose:
                print(f"  SKIP {name}: {e}")
            continue
        X = np.asarray(X, dtype=float)
        y = np.asarray(y)
        # drop rows with NaN
        mask = ~np.isnan(X).any(axis=1)
        X, y = X[mask], y[mask]
        if X.shape[0] > cap_n:
            # stratified subsample to cap_n for PH feasibility
            rng = np.random.RandomState(0)
            idx = rng.permutation(X.shape[0])[:cap_n]
            X, y = X[idx], y[idx]
        X = StandardScaler().fit_transform(X)
        # persist standardized artifact
        df = pd.DataFrame(X, columns=[f"f{j}" for j in range(X.shape[1])])
        df["label"] = y
        df.to_csv(os.path.join(STD_DIR, f"{name}.csv"), index=False)
        out.append((name, X, y))
        if verbose:
            print(f"  {name}: n={X.shape[0]}, d={X.shape[1]}, classes={len(np.unique(y))}")
    return out


if __name__ == "__main__":
    print("Loading + standardizing datasets (cap n=600)...")
    data = load_all()
    print(f"\nTotal: {len(data)} datasets ready in {STD_DIR}")
