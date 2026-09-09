"""E1/E2 analysis. All numbers derived from raw_*.csv (single source of truth).
Mean/std computed here via np.std from raw per-fold/per-seed rows, never stored."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

imp = pd.read_csv("raw_importance.csv")
down = pd.read_csv("raw_downstream.csv")
datasets = list(imp.dataset.unique())

print("=" * 70)
print("EXP 1: Complementarity -- Spearman rho(PAI, baseline) per dataset")
print("=" * 70)
print(f"{'dataset':<12} {'vs NRS':>8} {'vs Relief':>10} {'vs MI':>8} {'vs Var':>8}")
rho_nrs_all = []
for ds in datasets:
    sub = imp[imp.dataset == ds]
    # mean importance per attribute across seeds (bootstrap resamples)
    piv = sub.groupby(["method", "attribute_j"]).importance_score.mean().unstack(0)
    r_nrs = spearmanr(piv["pai"], piv["nrs"]).correlation
    r_rel = spearmanr(piv["pai"], piv["relieff"]).correlation
    r_mi = spearmanr(piv["pai"], piv["mutual_info"]).correlation
    r_var = spearmanr(piv["pai"], piv["variance"]).correlation
    rho_nrs_all.append(r_nrs)
    print(f"{ds:<12} {r_nrs:>8.3f} {r_rel:>10.3f} {r_mi:>8.3f} {r_var:>8.3f}")
print(f"{'MEAN':<12} {np.mean(rho_nrs_all):>8.3f}")
print(f"KC1 (rho(PAI,NRS)>0.9 on majority): "
      f"{sum(r>0.9 for r in rho_nrs_all)}/{len(datasets)} "
      f"-> {'FIRE/STOP' if sum(r>0.9 for r in rho_nrs_all)>len(datasets)/2 else 'PASS'}")

print("\n" + "=" * 70)
print("EXP 1b: PAI stability -- mean CV across seeds (bootstrap)")
print("=" * 70)
for ds in datasets:
    sub = imp[(imp.dataset == ds) & (imp.method == "pai")]
    g = sub.groupby("attribute_j").importance_score.agg(["mean", "std"])
    cv = (g["std"] / (g["mean"] + 1e-12)).mean()
    print(f"  {ds:<12} mean CV(PAI) = {cv:.3f}")

print("\n" + "=" * 70)
print("EXP 1c: Bound tightness -- PAI / [(K+1)*range], should be <=1")
print("=" * 70)
pai = imp[imp.method == "pai"].copy()
pai["ratio"] = pai.importance_score / (pai.pai_bound + 1e-12)
print(f"  max ratio (must be <=1): {pai.ratio.max():.4f}")
print(f"  mean ratio: {pai.ratio.mean():.4f}  (bound looseness)")
viol = (pai.importance_score > pai.pai_bound + 1e-9).sum()
print(f"  Thm 1 violations: {viol} (must be 0)")

print("\n" + "=" * 70)
print("EXP 2 (DECISIVE): best-k accuracy per method -- does PAI complement NRS?")
print("=" * 70)
# For each dataset+method: pick best k by mean acc across folds*seeds, report that mean+/-std
def best_k_acc(ds, method, clf):
    sub = down[(down.dataset == ds) & (down.method == method)]
    if sub.empty:
        return None
    g = sub.groupby("k_selected")[clf].agg(["mean", "std", "count"])
    bk = g["mean"].idxmax()
    return bk, g.loc[bk, "mean"], g.loc[bk, "std"], g.loc[bk, "count"]

for clf in ["acc_3nn", "acc_svm_rbf"]:
    print(f"\n--- classifier: {clf} (best-k mean+/-std) ---")
    print(f"{'dataset':<12} {'NRS':>16} {'PAI':>16} {'PAI_NRS':>16} {'ALL':>10}")
    win_union, tie_union, lose_union = 0, 0, 0
    for ds in datasets:
        nrs = best_k_acc(ds, "nrs", clf)
        pai_ = best_k_acc(ds, "pai", clf)
        uni = best_k_acc(ds, "pai_nrs", clf)
        allf = best_k_acc(ds, "all_features", clf)
        def fmt(x):
            return f"{x[1]*100:.1f}+/-{x[2]*100:.1f}(k{x[0]})" if x else "NA"
        print(f"{ds:<12} {fmt(nrs):>16} {fmt(pai_):>16} {fmt(uni):>16} "
              f"{allf[1]*100:.1f}" if allf else "")
        if nrs and uni:
            if uni[1] > nrs[1] + 1e-9: win_union += 1
            elif abs(uni[1] - nrs[1]) <= 1e-9: tie_union += 1
            else: lose_union += 1
    print(f"  PAI_NRS vs NRS (best-k): win={win_union}, tie={tie_union}, lose={lose_union}")

print("\n" + "=" * 70)
print("EXP 2b: paired test -- union vs NRS at matched k, per (dataset,seed,fold)")
print("=" * 70)
for clf in ["acc_3nn", "acc_svm_rbf"]:
    # align union and nrs at same dataset,seed,fold,k
    u = down[down.method == "pai_nrs"][["dataset","seed","fold","k_selected",clf]]
    n = down[down.method == "nrs"][["dataset","seed","fold","k_selected",clf]]
    m = u.merge(n, on=["dataset","seed","fold","k_selected"], suffixes=("_u","_n"))
    diff = m[f"{clf}_u"] - m[f"{clf}_n"]
    try:
        stat, p = wilcoxon(diff[diff != 0])
    except Exception:
        p = float("nan")
    print(f"  {clf}: mean(union-nrs)={diff.mean()*100:+.2f}pp, "
          f"median={diff.median()*100:+.2f}pp, "
          f"frac union>=nrs={np.mean(diff>=0):.2f}, Wilcoxon p={p:.2e}")
