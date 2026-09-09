"""E1 main runner. Produces two long-format CSVs, per-fold / per-seed raw values
(no pre-aggregated mean/std -- those are derived in E3 from these files).

Outputs:
  raw_importance.csv  - Exp 1 (ranking comparison + degeneracy + bound + stability)
  raw_downstream.csv  - Exp 2 (top-k reduct -> 3NN/SVM-RBF accuracy per fold)

Design honors research-commons/eval_harness/protocol.py:
  - StratifiedKFold(5, shuffle=True, random_state=seed), shared across methods
  - 3-NN + SVM-RBF default hyperparameters (probes, not tuned)
  - time_reduct_sec separated from time_eval_sec
  - importance computed on X_train only (leakage-free), memoized per fold so the
    k-sweep does not recompute PH.
"""
import os
import sys
import time
import hashlib
import warnings
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

sys.path.insert(0, os.path.dirname(__file__))
import importance as imp
from datasets import load_all

warnings.filterwarnings("ignore")

SEEDS = [0, 1, 2, 3, 4]
MAXDIM = 1
THRESH = 2.0
HERE = os.path.dirname(__file__)

RANKERS = ["pai", "nrs", "relieff", "mutual_info", "variance"]
# union methods for complementarity test (Exp 2 only)
UNION_METHODS = {"pai_nrs": ("pai", "nrs")}

# ---------- memoized importance (per exact X_train) ----------
_CACHE = {}

def _key(X, method):
    return (hashlib.md5(np.ascontiguousarray(X).tobytes()).hexdigest(), method)

def cached_importance(X, y, method):
    k = _key(X, method)
    if k not in _CACHE:
        t0 = time.perf_counter()
        _CACHE[k] = (imp.METHODS[method](X, y), time.perf_counter() - t0)
    return _CACHE[k]  # (scores, time_sec)


# ---------- Exp 1: importance on bootstrap resamples, per seed ----------
# Each seed = one 80%-without-replacement resample. Since all current methods are
# deterministic given their input, resampling is what produces genuine per-seed
# variation -> std across seeds is the real stability estimate (matches pilot).
BOOTSTRAP_FRAC = 0.8

def run_importance(datasets):
    from ripser import ripser
    rows = []
    for name, X, y in datasets:
        d = X.shape[1]
        n = X.shape[0]
        m = int(n * BOOTSTRAP_FRAC)
        for seed in SEEDS:
            rng = np.random.RandomState(seed)
            idx = rng.choice(n, size=m, replace=False)
            Xb, yb = X[idx], y[idx]
            for method in RANKERS:
                t0 = time.perf_counter()
                scores = imp.METHODS[method](Xb, yb)
                dt = time.perf_counter() - t0

                if method == "pai":
                    dgm = ripser(Xb, maxdim=MAXDIM, thresh=THRESH)["dgms"]
                    n_h0, n_h1 = len(dgm[0]), len(dgm[1])
                    ranges = Xb.max(axis=0) - Xb.min(axis=0)
                else:
                    n_h0 = n_h1 = -1
                    ranges = None

                for j in range(d):
                    rows.append({
                        "dataset": name, "n": n, "d": d, "n_resample": m,
                        "seed": seed, "method": method, "attribute_j": j,
                        "importance_score": float(scores[j]),
                        "pai_bound": float((MAXDIM + 1) * ranges[j]) if ranges is not None else -1.0,
                        "n_pts_dgm_H0": n_h0, "n_pts_dgm_H1": n_h1,
                        "thresh": THRESH, "maxdim": MAXDIM,
                        "time_method_sec": dt,
                    })
    return pd.DataFrame(rows)


# ---------- Exp 2: downstream top-k reduct via 5-fold CV ----------
def _eval_fold(X_tr, y_tr, X_te, y_te, sel):
    Xtr, Xte = X_tr[:, sel], X_te[:, sel]
    t0 = time.perf_counter()
    knn = KNeighborsClassifier(n_neighbors=3).fit(Xtr, y_tr)
    acc_3nn = knn.score(Xte, y_te)
    svm = SVC(kernel="rbf").fit(Xtr, y_tr)
    acc_svm = svm.score(Xte, y_te)
    return acc_3nn, acc_svm, time.perf_counter() - t0

def run_downstream(datasets):
    rows = []
    for name, X, y in datasets:
        d = X.shape[1]
        ks = list(range(1, d + 1))
        for seed in SEEDS:
            _CACHE.clear()  # cache is per (X_train); clear between seeds to bound memory
            skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
            for fold, (tr, te) in enumerate(skf.split(X, y), start=1):
                X_tr, X_te = X[tr], X[te]
                y_tr, y_te = y[tr], y[te]

                # precompute importance per ranker on THIS fold's train (leakage-free)
                fold_scores = {}
                fold_time = {}
                for method in RANKERS:
                    sc, tsec = cached_importance(X_tr, y_tr, method)
                    fold_scores[method] = sc
                    fold_time[method] = tsec

                # single-method rankers
                for method in RANKERS:
                    order = np.argsort(-fold_scores[method])  # desc importance
                    for k in ks:
                        sel = order[:k]
                        acc_3nn, acc_svm, t_eval = _eval_fold(X_tr, y_tr, X_te, y_te, sel)
                        rows.append({
                            "dataset": name, "n": X.shape[0], "d": d,
                            "seed": seed, "fold": fold, "method": method,
                            "k_selected": k,
                            "selected_features": "|".join(map(str, sorted(sel.tolist()))),
                            "acc_3nn": acc_3nn, "acc_svm_rbf": acc_svm,
                            "time_reduct_sec": fold_time[method],
                            "time_eval_sec": t_eval,
                        })

                # union methods (complementarity): interleave top from each
                for uname, (m1, m2) in UNION_METHODS.items():
                    o1 = np.argsort(-fold_scores[m1])
                    o2 = np.argsort(-fold_scores[m2])
                    for k in ks:
                        # interleave until we have k distinct features
                        sel, i1, i2 = [], 0, 0
                        while len(sel) < k:
                            if i1 < len(o1) and o1[i1] not in sel:
                                sel.append(int(o1[i1]))
                            i1 += 1
                            if len(sel) >= k:
                                break
                            if i2 < len(o2) and o2[i2] not in sel:
                                sel.append(int(o2[i2]))
                            i2 += 1
                            if i1 >= len(o1) and i2 >= len(o2):
                                break
                        sel = np.array(sel[:k])
                        acc_3nn, acc_svm, t_eval = _eval_fold(X_tr, y_tr, X_te, y_te, sel)
                        rows.append({
                            "dataset": name, "n": X.shape[0], "d": d,
                            "seed": seed, "fold": fold, "method": uname,
                            "k_selected": k,
                            "selected_features": "|".join(map(str, sorted(sel.tolist()))),
                            "acc_3nn": acc_3nn, "acc_svm_rbf": acc_svm,
                            "time_reduct_sec": fold_time[m1] + fold_time[m2],
                            "time_eval_sec": t_eval,
                        })

                # full feature set (baseline, k=d) is already covered by k=d rankers,
                # but log explicit ALL for clarity
                acc_3nn, acc_svm, t_eval = _eval_fold(
                    X_tr, y_tr, X_te, y_te, np.arange(d))
                rows.append({
                    "dataset": name, "n": X.shape[0], "d": d,
                    "seed": seed, "fold": fold, "method": "all_features",
                    "k_selected": d,
                    "selected_features": "|".join(map(str, range(d))),
                    "acc_3nn": acc_3nn, "acc_svm_rbf": acc_svm,
                    "time_reduct_sec": 0.0, "time_eval_sec": t_eval,
                })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    only = sys.argv[2] if len(sys.argv) > 2 else None

    print("Loading datasets...")
    datasets = load_all(verbose=False)
    if only:
        datasets = [d for d in datasets if d[0] == only]
    print(f"  {len(datasets)} datasets: {[d[0] for d in datasets]}")

    if mode in ("all", "importance"):
        print("Running Exp 1 (importance)...")
        t0 = time.time()
        df_imp = run_importance(datasets)
        df_imp.to_csv(os.path.join(HERE, "raw_importance.csv"), index=False)
        print(f"  raw_importance.csv: {len(df_imp)} rows, {time.time()-t0:.1f}s")

    if mode in ("all", "downstream"):
        print("Running Exp 2 (downstream)...")
        t0 = time.time()
        df_down = run_downstream(datasets)
        df_down.to_csv(os.path.join(HERE, "raw_downstream.csv"), index=False)
        print(f"  raw_downstream.csv: {len(df_down)} rows, {time.time()-t0:.1f}s")

    print("Done.")
