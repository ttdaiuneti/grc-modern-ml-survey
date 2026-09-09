"""Analyze structure-preservation. Aggregate over k (mean across k=1..d-1; exclude
k=d where all methods trivially equal). Win/tie/loss of PAI vs each baseline per
dataset, on INDEPENDENT metrics (trustworthiness, knn_overlap, cluster_ari).
wass_persist reported separately (PAI-favoring)."""
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

df = pd.read_csv("raw_structure.csv")
datasets = list(df.dataset.unique())
METHODS = ["nrs", "relieff", "mutual_info", "variance"]
# higher-is-better metrics; wass_persist is lower-is-better
INDEP = ["trustworthiness", "knn_overlap", "cluster_ari"]

def agg_over_k(sub):
    # mean over k < d (exclude trivial k=d)
    d = sub.d.iloc[0]
    return sub[sub.k_selected < d]

print("="*74)
print("PAI vs baselines on INDEPENDENT structure metrics (mean over k<d, per dataset)")
print("PAI wins = higher trustworthiness/knn_overlap/cluster_ari")
print("="*74)
for metric in INDEP:
    print(f"\n--- {metric} ---")
    print(f"{'dataset':<12} {'PAI':>7} {'NRS':>7} {'Relief':>7} {'MI':>7} {'Var':>7}  PAI_best?")
    pai_best_count = 0
    for ds in datasets:
        sub = agg_over_k(df[df.dataset == ds])
        means = sub.groupby("method")[metric].mean()
        vals = {m: means.get(m, np.nan) for m in ["pai"] + METHODS}
        pai_best = vals["pai"] >= max(vals[m] for m in METHODS) - 1e-9
        pai_best_count += pai_best
        print(f"{ds:<12} {vals['pai']:>7.3f} {vals['nrs']:>7.3f} {vals['relieff']:>7.3f} "
              f"{vals['mutual_info']:>7.3f} {vals['variance']:>7.3f}  {'YES' if pai_best else 'no'}")
    print(f"  --> PAI is best on {pai_best_count}/{len(datasets)} datasets")

print("\n" + "="*74)
print("Paired test: PAI vs NRS at matched k (per dataset,k), independent metrics")
print("="*74)
dmap = df.groupby('dataset').d.first().to_dict()
for metric in INDEP:
    p = df[df.method == "pai"][["dataset","k_selected",metric]]
    n = df[df.method == "nrs"][["dataset","k_selected",metric]]
    m = p.merge(n, on=["dataset","k_selected"], suffixes=("_pai","_nrs"))
    m = m[m.k_selected < m.dataset.map(dmap)]  # exclude trivial k=d
    diff = m[f"{metric}_pai"] - m[f"{metric}_nrs"]
    try:
        _, pval = wilcoxon(diff[diff != 0])
    except Exception:
        pval = float("nan")
    print(f"  {metric:<16}: mean(PAI-NRS)={diff.mean():+.4f}, "
          f"frac PAI>=NRS={np.mean(diff>=0):.2f}, Wilcoxon p={pval:.2e}")

print("\n" + "="*74)
print("SECONDARY (PAI-favoring): wass_persist, lower=better")
print("="*74)
print(f"{'dataset':<12} {'PAI':>8} {'NRS':>8} {'best?':>6}")
pai_wins = 0
for ds in datasets:
    sub = agg_over_k(df[df.dataset == ds])
    means = sub.groupby("method")["wass_persist"].mean()
    pai_v = means.get("pai")
    others_min = min(means.get(m) for m in METHODS)
    win = pai_v <= others_min + 1e-9
    pai_wins += win
    print(f"{ds:<12} {pai_v:>8.2f} {means.get('nrs'):>8.2f} {'YES' if win else 'no':>6}")
print(f"  --> PAI lowest wass on {pai_wins}/{len(datasets)}")
