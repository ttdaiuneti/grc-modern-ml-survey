"""MAJOR-9 discriminating test: does PAI's knn_overlap advantage track the
neighbourhood scale, as Pattern C's explanation requires?"""
import os
DATA = os.environ.get("GRC_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "data") + os.sep)
import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "raw_knn_scale.csv"))
DATASETS = ['iris', 'wine', 'ionosphere', 'sonar', 'glass',
            'ecoli', 'heart', 'parkinsons', 'seeds', 'wdbc']

print("PAI's filtration scale per dataset (mean neighbours within Rips thresh 2.0)")
scale = df.groupby('dataset')['k_pai_scale'].first()
for d in DATASETS:
    print(f"   {d:11s} k_pai = {scale[d]:6.1f}")

print("\nPAI vs NRS on knn_overlap, aggregated over k<d, dataset-level Wilcoxon (n=10)")
print(f"{'K':>4} {'PAI':>7} {'NRS':>7} {'delta':>8} {'wins':>6} {'p':>8}")
rows = []
for K in sorted(df.knn_K.unique()):
    P, N = [], []
    for d in DATASETS:
        sub = df[(df.dataset == d) & (df.knn_K == K)]
        sub = sub[sub.k_selected < sub['d'].iloc[0]]
        m = sub.groupby('method')['knn_overlap'].mean()
        P.append(m['pai']); N.append(m['nrs'])
    P, N = np.array(P), np.array(N)
    pv = stats.wilcoxon(P, N).pvalue
    rows.append((K, P, N, pv))
    print(f"{K:>4} {P.mean():7.3f} {N.mean():7.3f} {P.mean()-N.mean():+8.3f} "
          f"{int((P>N).sum()):5d}/10 {pv:8.3f}")

print("\nPer-dataset advantage (PAI - NRS) by K, against that dataset's k_pai scale")
print(f"{'dataset':11s} {'k_pai':>7} " + " ".join(f"{'K='+str(K):>8}" for K, *_ in rows)
      + f" {'argmax K':>9}")
adv = {}
for i, d in enumerate(DATASETS):
    a = [P[i] - N[i] for _, P, N, _ in rows]
    adv[d] = a
    best = rows[int(np.argmax(a))][0]
    print(f"{d:11s} {scale[d]:7.1f} " + " ".join(f"{v:+8.3f}" for v in a) + f" {best:9d}")

print("\nDiscriminating test: is the advantage largest where K matches k_pai?")
Ks = np.array([K for K, *_ in rows], float)
best_K = np.array([Ks[int(np.argmax(adv[d]))] for d in DATASETS])
kpai = np.array([scale[d] for d in DATASETS])
ok = kpai > 0
r, p = stats.spearmanr(kpai[ok], best_K[ok])
print(f"   Spearman(k_pai, argmax-K) over {int(ok.sum())} datasets with k_pai>0: "
      f"rho = {r:+.3f}, p = {p:.3f}")
print("   (Pattern C's scale explanation predicts rho > 0: the advantage should")
print("    peak at the K that matches the scale PAI's filtration actually sees.)")

# advantage vs scale mismatch, pooled
mm, aa = [], []
for i, d in enumerate(DATASETS):
    if scale[d] <= 0:
        continue
    for j, K in enumerate(Ks):
        mm.append(abs(np.log(K) - np.log(scale[d]))); aa.append(adv[d][j])
r2, p2 = stats.spearmanr(mm, aa)
print(f"   Spearman(|log K - log k_pai|, advantage) pooled, n={len(mm)}: "
      f"rho = {r2:+.3f}, p = {p2:.3f}")
print("   (prediction: rho < 0 -- advantage decays as the scales are mismatched)")
