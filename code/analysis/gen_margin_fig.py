"""
Generate Figure: best-k minus all-features 3-NN accuracy margin per dataset.
Output: figures/margin_plot.pdf
"""
import os, matplotlib
matplotlib.use("Agg")
# Embed real (TrueType) fonts, not Type 3 bitmaps, so the PDF passes
# publisher preflight.
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

OUT = os.environ.get("GRC_FIGURES_OUT", "figures")
os.makedirs(OUT, exist_ok=True)

DATA = os.environ.get("GRC_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data") + os.sep)
ds = pd.read_csv(os.path.join(DATA, "raw_downstream.csv"))

DATASETS = ['iris','wine','ionosphere','sonar','glass',
            'ecoli','heart','parkinsons','seeds','wdbc']
NAME = {'iris':'Iris','wine':'Wine','ionosphere':'Ionosphere',
        'sonar':'Sonar','glass':'Glass','ecoli':'Ecoli',
        'heart':'Heart','parkinsons':'Parkinsons','seeds':'Seeds','wdbc':'WDBC'}

from scipy import stats

margins, all_accs, best_accs, labels, pvals, pcorr = [], [], [], [], [], []


def corrected_resampled_t(diff, test_train_ratio=0.25):
    """Corrected resampled t-test (Nadeau & Bengio 2003), as in gen_tables.py."""
    J, v = len(diff), np.var(diff, ddof=1)
    if v == 0:
        return 1.0
    t = np.mean(diff) / np.sqrt((1.0 / J + test_train_ratio) * v)
    return 2 * stats.t.sf(abs(t), J - 1)


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
    pcorr.append(corrected_resampled_t(diff.values))
    all_accs.append(all_f[j].mean() * 100)
    best_accs.append(best[j].mean() * 100)
    labels.append(NAME[d_name])

# Holm step-down correction over the ten datasets
def holm(pv):
    order, prev, out = np.argsort(pv), 0.0, [0.0] * len(pv)
    for rank, i in enumerate(order):
        prev = min(1.0, max(prev, (len(pv) - rank) * pv[i]))
        out[i] = prev
    return out

p_holm = holm(pvals)        # naive fold-level Wilcoxon
p_corr = holm(pcorr)        # corrected resampled t-test

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 3.4))

x = np.arange(len(labels))
SIG = 0.05

ax.axhline(0, color='gray', linewidth=0.8, linestyle='--')

# Lollipop stems: colour by the corrected resampled t-test (Holm); an open
# triangle marks gains that only the naive fold-level Wilcoxon separates.
for xi, m, ph, pc in zip(x, margins, p_holm, p_corr):
    color = '#2166ac' if pc < SIG else '#aaaaaa'
    ax.vlines(xi, 0, m, colors=color, linewidth=1.8)
    ax.plot(xi, m, 'o', color=color, markersize=7, zorder=4)
    if ph < SIG and pc >= SIG:
        ax.plot(xi, m + 0.65, marker='v', markersize=5.5, markerfacecolor='none',
                markeredgecolor='#b2182b', linestyle='none', zorder=5)

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

from matplotlib.lines import Line2D
handles = [mpatches.Patch(color='#aaaaaa',
                          label='Not separated from zero (corrected resampled $t$, Holm)'),
           Line2D([], [], marker='v', markersize=5.5, markerfacecolor='none',
                  markeredgecolor='#b2182b', linestyle='none',
                  label='Separated only by fold-level Wilcoxon (Holm $p<0.05$)')]
if any(pc < SIG for pc in p_corr):
    handles.insert(0, mpatches.Patch(color='#2166ac',
                   label='Gain separated (corrected resampled $t$, Holm $p<0.05$)'))
ax.legend(handles=handles, fontsize=7.5, loc='upper right', framealpha=0.9)

plt.tight_layout(pad=0.4)
plt.savefig(f"{OUT}/margin_plot.pdf", dpi=300, bbox_inches="tight")
plt.savefig(f"{OUT}/margin_plot.png", dpi=200, bbox_inches="tight")
print(f"Saved {OUT}/margin_plot.pdf and .png")
for l, m, a, b, ph, pc in zip(labels, margins, all_accs, best_accs, p_holm, p_corr):
    print(f"  {l:14s} all={a:.1f}%  best={b:.1f}%  margin={m:+.2f}pp  "
          f"p_wilcoxon_holm={ph:.4f}  p_corrected_holm={pc:.4f}")
