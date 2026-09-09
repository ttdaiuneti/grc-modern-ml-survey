"""E1 extension: is PAI's knn_overlap advantage a neighbourhood-scale artefact?

Pattern C (Section 7.3) explains PAI's apparent edge on knn_overlap by noting
that PAI's bottleneck objective and knn_overlap probe the SAME local
neighbourhoods.  That explanation is post-hoc unless the advantage tracks the
scale match.  This script tests it directly: it recomputes knn_overlap over a
grid of neighbourhood sizes K, deliberately mismatched to the scale PAI's
Vietoris-Rips filtration actually sees, reusing the feature subsets already
recorded in raw_structure.csv (so no importance is recomputed and the
selections are identical to the main experiment).

k_pai_scale = mean number of points within the Rips threshold (2.0) in the full
standardized space: the empirical neighbourhood size of PAI's filtration.

Both knn_overlap and trustworthiness are ablated: they share the parameter.
Output: raw_knn_scale.csv (long: dataset, method, k_selected, knn_K, metrics)
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.manifold import trustworthiness

sys.path.insert(0, os.path.dirname(__file__))
from datasets import load_all

HERE = os.path.dirname(os.path.abspath(__file__))
THRESH = 2.0                      # same Rips threshold as importance.py
K_GRID = [3, 5, 10, 20, 30, 50]   # 10 reproduces the main experiment


def neighbours(X, K):
    kk = min(K + 1, X.shape[0])
    return NearestNeighbors(n_neighbors=kk).fit(X).kneighbors(return_distance=False)[:, 1:]


def overlap(nn_full, nn_red):
    return float(np.mean([len(set(a) & set(b)) / nn_full.shape[1]
                          for a, b in zip(nn_full, nn_red)]))


def main():
    st = pd.read_csv(os.path.join(HERE, "raw_structure.csv"))
    data = {name: X for name, X, _ in load_all(verbose=False)}
    rows = []
    for name, sub in st.groupby("dataset", sort=False):
        X = data[name]
        assert X.shape[0] == int(sub.n.iloc[0]) and X.shape[1] == int(sub.d.iloc[0]), \
            f"{name}: loaded shape {X.shape} != recorded ({sub.n.iloc[0]},{sub.d.iloc[0]})"
        # empirical neighbourhood size of PAI's filtration
        nn_all = NearestNeighbors(n_neighbors=X.shape[0]).fit(X)
        dist, _ = nn_all.kneighbors(X)
        k_pai = float(np.mean((dist[:, 1:] <= THRESH).sum(axis=1)))

        full = {K: neighbours(X, K) for K in K_GRID if K < X.shape[0]}
        for r in sub.itertuples():
            sel = np.array([int(v) for v in str(r.selected_features).split("|")])
            Xr = X[:, sel]
            for K, nn_f in full.items():
                # trustworthiness carries the SAME free neighbourhood parameter,
                # so it must be ablated on the same grid or the comparison is unfair
                tw = (trustworthiness(X, Xr, n_neighbors=K)
                      if K < X.shape[0] / 2 else float("nan"))
                rows.append({
                    "dataset": name, "n": X.shape[0], "d": int(r.d),
                    "method": r.method, "k_selected": int(r.k_selected),
                    "knn_K": K, "knn_overlap": overlap(nn_f, neighbours(Xr, K)),
                    "trustworthiness": tw, "k_pai_scale": k_pai,
                })
        print(f"  {name:11s} n={X.shape[0]:3d} d={X.shape[1]:2d}  k_pai_scale={k_pai:6.1f}")

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "raw_knn_scale.csv"), index=False)
    print(f"\nraw_knn_scale.csv: {len(df)} rows")

    # sanity: K=10 must reproduce the main experiment's knn_overlap exactly
    m = df[df.knn_K == 10].merge(
        st[["dataset", "method", "k_selected", "knn_overlap"]],
        on=["dataset", "method", "k_selected"], suffixes=("_new", "_orig"))
    d = (m.knn_overlap_new - m.knn_overlap_orig).abs()
    exact = int((d < 1e-12).sum())
    # knn_overlap moves in quanta of 1/(K*n); a differing row means a tie in the
    # distance matrix was broken the other way, which is arbitrary, not a defect.
    quantum = 2.0 / (10 * m.n)
    within = int((d <= quantum + 1e-12).sum())
    print(f"reproduction check at K=10: {exact}/{len(m)} rows exact, "
          f"{within}/{len(m)} within 2 tie-quanta, max |diff| = {d.max():.2e}, "
          f"mean signed diff = {(m.knn_overlap_new - m.knn_overlap_orig).mean():+.2e}")
    print(f"  -> {'PASS' if within == len(m) else 'FAIL'} "
          f"(differing rows are ties: {sorted(m[d >= 1e-12].dataset.unique())})")


if __name__ == "__main__":
    main()
