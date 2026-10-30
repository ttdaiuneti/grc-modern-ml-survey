"""Sensitivity of the PAI-vs-NRS comparison to the two fixed settings of E1
(added in revision, reviewer request): the NRS neighbourhood size k (default 7)
and the persistence configuration of PAI (default maxdim=1, thresh=2.0).

Same datasets, seeds, 80% subsamples and StratifiedKFold splits as run_e1.py,
so the default configurations reproduce raw_importance.csv / raw_downstream.csv.

Outputs (one CSV per dataset x method x config, resumable; concatenated by
analysis/analyze_ablation.py):
  data/ablation/imp_<dataset>_<method>_<config>.csv   importance on the 80% subsamples
  data/ablation/down_<dataset>_<method>_<config>.csv  top-k 3-NN / SVM-RBF accuracy per fold

Usage: python3 run_ablation.py [n_workers]
"""
import os
import sys
import time
import warnings
from multiprocessing import Pool
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, os.path.dirname(__file__))
import importance as imp
from datasets import load_all
from run_e1 import SEEDS, BOOTSTRAP_FRAC, _eval_fold

warnings.filterwarnings("ignore")

NRS_K = [3, 5, 7, 11, 15]
PAI_CFG = [(1, 2.0), (0, 2.0), (1, 1.5), (1, 3.0), (0, np.inf)]
OUT = os.environ.get("GRC_ABLATION",
                     os.path.join(os.path.dirname(__file__), "..", "..", "data", "ablation"))


def cfg_name(method, cfg):
    if method == "nrs":
        return f"k{cfg}"
    maxdim, thresh = cfg
    return f"md{maxdim}_t{'inf' if np.isinf(thresh) else thresh}"


def scorer(method, cfg):
    if method == "nrs":
        return lambda X, y: imp.nrs_scores(X, y, k=cfg)
    maxdim, thresh = cfg
    return lambda X, y: imp.pai_scores(X, y, maxdim=maxdim, thresh=thresh)


def run_unit(args):
    name, X, y, method, cfg = args
    tag = f"{name}_{method}_{cfg_name(method, cfg)}"
    f_imp = os.path.join(OUT, f"imp_{tag}.csv")
    f_down = os.path.join(OUT, f"down_{tag}.csv")
    if os.path.exists(f_imp) and os.path.exists(f_down):
        return tag, "skip"
    score = scorer(method, cfg)
    n, d = X.shape
    t_start = time.perf_counter()

    rows = []
    for seed in SEEDS:
        rng = np.random.RandomState(seed)
        idx = rng.choice(n, size=int(n * BOOTSTRAP_FRAC), replace=False)
        s = score(X[idx], y[idx])
        for j in range(d):
            rows.append(dict(dataset=name, seed=seed, method=method,
                             config=cfg_name(method, cfg), attribute_j=j,
                             importance_score=float(s[j])))
    imp_df = pd.DataFrame(rows)

    rows = []
    for seed in SEEDS:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
        for fold, (tr, te) in enumerate(skf.split(X, y), start=1):
            t0 = time.perf_counter()
            s = score(X[tr], y[tr])
            t_red = time.perf_counter() - t0
            order = np.argsort(-s)
            for k in range(1, d + 1):
                a3, asvm, t_ev = _eval_fold(X[tr], y[tr], X[te], y[te], order[:k])
                rows.append(dict(dataset=name, d=d, seed=seed, fold=fold,
                                 method=method, config=cfg_name(method, cfg),
                                 k_selected=k, acc_3nn=a3, acc_svm_rbf=asvm,
                                 time_reduct_sec=t_red, time_eval_sec=t_ev))
    down_df = pd.DataFrame(rows)
    imp_df.to_csv(f_imp, index=False)      # written only once both parts finished
    down_df.to_csv(f_down, index=False)
    return tag, f"{time.perf_counter() - t_start:.0f}s"


if __name__ == "__main__":
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    os.makedirs(OUT, exist_ok=True)
    data = load_all(verbose=False)
    units = [(nm, X, y, "nrs", k) for nm, X, y in data for k in NRS_K]
    units += [(nm, X, y, "pai", c) for nm, X, y in data for c in PAI_CFG]
    # expensive PAI units first so the pool stays busy
    units.sort(key=lambda u: (u[3] != "pai", -u[1].shape[0] * u[1].shape[1]))
    with Pool(workers) as pool:
        for tag, status in pool.imap_unordered(run_unit, units):
            print(f"{tag}: {status}", flush=True)
