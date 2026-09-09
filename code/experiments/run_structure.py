"""E1 (reframed): structure-preservation evaluation of feature selectors.

Question: among selectors, which best PRESERVES the intrinsic structure of the
data when reducing to top-k features? PAI is designed for this; the others are
discriminative (label-aware) or scale-based.

To avoid circularity, the primary evaluation metrics are NOT the persistence
distance PAI optimizes, but INDEPENDENT structure metrics:
  - trustworthiness (local neighborhood preservation, Venna-Kaski / sklearn)
  - knn_overlap (mean fraction of shared k-NN between full and reduced space)
  - cluster_ari (KMeans on full vs reduced, adjusted Rand index)
We also report wass_persist (Wasserstein distance of subset diagram vs full) as a
SECONDARY, PAI-favoring sanity metric, clearly labeled.

Importance computed on full standardized X (label-free methods truly label-free).
Output: raw_structure.csv, long format, per (dataset, method, k, metric).
"""
import os, sys, time, warnings
import numpy as np
import pandas as pd
from sklearn.manifold import trustworthiness
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from ripser import ripser
from persim import wasserstein

sys.path.insert(0, os.path.dirname(__file__))
import importance as imp
from datasets import load_all

warnings.filterwarnings("ignore")
HERE = os.path.dirname(__file__)
KNN = 10
MAXDIM, THRESH = 1, 2.0
METHODS = ["pai", "nrs", "relieff", "mutual_info", "variance"]


def knn_overlap(X_full, X_red, k=KNN):
    n = X_full.shape[0]
    kk = min(k + 1, n)
    nn_f = NearestNeighbors(n_neighbors=kk).fit(X_full).kneighbors(return_distance=False)[:, 1:]
    nn_r = NearestNeighbors(n_neighbors=kk).fit(X_red).kneighbors(return_distance=False)[:, 1:]
    ov = [len(set(nn_f[i]) & set(nn_r[i])) / nn_f.shape[1] for i in range(n)]
    return float(np.mean(ov))


def cluster_ari(X_full, X_red, n_clusters, seed=0):
    c_f = KMeans(n_clusters=n_clusters, n_init=5, random_state=seed).fit_predict(X_full)
    c_r = KMeans(n_clusters=n_clusters, n_init=5, random_state=seed).fit_predict(X_red)
    return adjusted_rand_score(c_f, c_r)


def wass_persist(X_full, X_red):
    df = ripser(X_full, maxdim=MAXDIM, thresh=THRESH)["dgms"]
    dr = ripser(X_red, maxdim=MAXDIM, thresh=THRESH)["dgms"]
    return sum(wasserstein(df[k], dr[k]) for k in range(MAXDIM + 1))


def main():
    datasets = load_all(verbose=False)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    if only:
        datasets = [d for d in datasets if d[0] == only]
    rows = []
    for name, X, y in datasets:
        d = X.shape[1]
        n_classes = len(np.unique(y))
        # importance on full X (once per method)
        scores, itime = {}, {}
        for m in METHODS:
            t0 = time.perf_counter()
            scores[m] = imp.METHODS[m](X, y)
            itime[m] = time.perf_counter() - t0
        for m in METHODS:
            order = np.argsort(-scores[m])
            for k in range(1, d + 1):
                sel = np.sort(order[:k])
                Xr = X[:, sel]
                tw = trustworthiness(X, Xr, n_neighbors=min(KNN, X.shape[0] - 1))
                ko = knn_overlap(X, Xr)
                ari = cluster_ari(X, Xr, n_classes)
                wp = wass_persist(X, Xr)
                rows.append({
                    "dataset": name, "n": X.shape[0], "d": d, "n_classes": n_classes,
                    "method": m, "k_selected": k,
                    "selected_features": "|".join(map(str, sel.tolist())),
                    "trustworthiness": tw, "knn_overlap": ko, "cluster_ari": ari,
                    "wass_persist": wp, "importance_time_sec": itime[m],
                })
        print(f"  done {name} (n={X.shape[0]}, d={d})")
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "raw_structure.csv"), index=False)
    print(f"raw_structure.csv: {len(df)} rows")


if __name__ == "__main__":
    main()
