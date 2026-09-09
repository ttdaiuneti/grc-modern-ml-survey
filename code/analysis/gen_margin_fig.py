"""
Generate Figure: best-k minus all-features 3-NN accuracy margin per dataset.
Output: figures/margin_plot.pdf
"""
import os
DATA = os.environ.get("GRC_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "data") + os.sep)
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

os.makedirs("figures", exist_ok=True)

RAW_DS = DATA + "raw_downstream.csv"
ds = pd.read_csv(RAW_DS)

DATASETS = ['iris','wine','ionosphere','sonar','glass',
            'ecoli','heart','parkinsons','seeds','wdbc']
NAME = {'iris':'Iris','wine':'Wine','ionosphere':'Ionosphere',
        'sonar':'Sonar','glass':'Glass','ecoli':'Ecoli',
        'heart':'Heart','parkinsons':'Parkinsons','seeds':'Seeds','wdbc':'WDBC'}

from scipy import stats

margins, all_accs, best_accs, labels, pvals = [], [], [], [], []

for d_name in DATASETS:
    sub = ds[ds.dataset == d_name]
    all_f = sub[sub.method == 'all_features'].set_index(['seed', 'fold'])['acc_3nn']
    per_mk = sub.groupby(['method', 'k_selected'])['acc_3nn'].mean()
    bi = per_mk.idxmax()
    best = sub[(sub.method == bi[0]) & (sub.k_selected == bi[1])] \
             .set_index(['seed', 'fold'])['acc_3nn']
    j = best.index.intersection(all_f.index)
    diff = best[j] - all_f[j]
    margins.append(diff.mean() * 100)
    pvals.append(1.0 if diff.abs().sum() == 0 else stats.wilcoxon(best[j], all_f[j]).pvalue)
    all_accs.append(all_f[j].mean() * 100)
    best_accs.append(best[j].mean() * 100)
    labels.append(NAME[d_name])

# Holm step-down correction over the ten datasets
order, prev, p_holm = np.argsort(pvals), 0.0, [0.0] * len(pvals)
for rank, i in enumerate(order):
    prev = min(1.0, max(prev, (len(pvals) - rank) * pvals[i]))
    p_holm[i] = prev

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 3.4))

x = np.arange(len(labels))
SIG = 0.05

ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')

# Lollipop stems: colour by Holm-corrected significance, not by an eyeballed band
for xi, m, ph in zip(x, margins, p_holm):
    color = '#2166ac' if ph < SIG else '#aaaaaa'
    ax.vlines(xi, 0, m, colors=color, linewidth=1.8)
    ax.plot(xi, m, 'o', color=color, markersize=7, zorder=4)
    if ph < SIG:
        ax.annotate(f'$p$={ph:.3f}' if ph >= 0.001 else '$p<$0.001',
                    xy=(xi, m), xytext=(0, 6), textcoords='offset points',
                    ha='center', fontsize=6.5, color='#2166ac')

# Annotate Heart (k*=d)
heart_idx = labels.index('Heart')
ax.annotate('$k^*=d$\n(no reduction)', xy=(heart_idx, margins[heart_idx]),
            xytext=(heart_idx - 0.5, margins[heart_idx] - 1.4),
            fontsize=7, color='#888888',
            arrowprops=dict(arrowstyle='->', color='#aaaaaa', lw=0.8))

ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=8.5)
ax.set_ylabel('Best-$k$ acc. $-$ all-features acc. (pp)', fontsize=9)
ax.set_ylim(-1.5, max(margins) + 1.9)
ax.yaxis.grid(True, linewidth=0.4, alpha=0.5)
ax.set_axisbelow(True)
ax.spines[["top", "right"]].set_visible(False)

blue_patch = mpatches.Patch(color='#2166ac',
                            label='Gain significant (paired Wilcoxon, Holm $p<0.05$)')
gray_patch = mpatches.Patch(color='#aaaaaa',
                            label='Gain not distinguishable from zero')
ax.legend(handles=[blue_patch, gray_patch],
          fontsize=7.5, loc='upper right', framealpha=0.9)

plt.tight_layout(pad=0.4)
plt.savefig("figures/margin_plot.pdf", dpi=300, bbox_inches="tight")
plt.savefig("figures/margin_plot.png", dpi=200, bbox_inches="tight")
print("Saved figures/margin_plot.pdf and .png")
for l, m, a, b, ph in zip(labels, margins, all_accs, best_accs, p_holm):
    flag = "SIG" if ph < 0.05 else "ns"
    print(f"  {l:14s} all={a:.1f}%  best={b:.1f}%  margin={m:+.2f}pp  "
          f"p_holm={ph:.4f}  {flag}")
