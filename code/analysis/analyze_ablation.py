"""Sensitivity of the PAI-vs-NRS comparison to the settings fixed in E1:
NRS neighbourhood size k and PAI's persistence configuration.

Reads data/ablation/{imp,down}_*.csv (from experiments/run_ablation.py) and the
original raw_downstream.csv (variance null baseline).  Writes
tables/tab_sensitivity.tex (sn-jnl surveytable layout) and prints the inline
statistics quoted in the manuscript.

All accuracies are means over k_selected < d, first per dataset (25 runs x
the k grid), then over the ten datasets, exactly as for the headline numbers
of Section 7.4.  Paired tests are Wilcoxon signed-rank over the ten
dataset-level values (the dataset is the independent unit).
"""
import glob
import os
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.environ.get("GRC_DATA", os.path.join(HERE, "..", "..", "data"))
OUT = os.environ.get("GRC_TABLES_OUT", "tables")
ABL = os.path.join(DATA, "ablation")

DATASETS = ['iris', 'wine', 'ionosphere', 'sonar', 'glass',
            'ecoli', 'heart', 'parkinsons', 'seeds', 'wdbc']
NRS_K = ["k3", "k5", "k7", "k11", "k15"]
PAI_CFG = ["md1_t2.0", "md0_t2.0", "md1_t1.5", "md1_t3.0", "md0_tinf"]
PAI_LABEL = {"md1_t2.0": r"$H_0{+}H_1$, $\varepsilon_{\max}=2$ (default)",
             "md0_t2.0": r"$H_0$ only, $\varepsilon_{\max}=2$",
             "md1_t1.5": r"$H_0{+}H_1$, $\varepsilon_{\max}=1.5$",
             "md1_t3.0": r"$H_0{+}H_1$, $\varepsilon_{\max}=3$",
             "md0_tinf": r"$H_0$ only, no truncation"}

imp = pd.concat(pd.read_csv(f) for f in glob.glob(os.path.join(ABL, "imp_*.csv")))
down = pd.concat(pd.read_csv(f) for f in glob.glob(os.path.join(ABL, "down_*.csv")))
raw = pd.read_csv(os.path.join(DATA, "raw_downstream.csv"))


def have(method, cfg):
    return set(down[(down.method == method) & (down.config == cfg)].dataset) >= set(DATASETS)


def acc(method, cfg, col="acc_3nn"):
    """Dataset-level mean accuracy over k_selected < d, in DATASETS order."""
    s = down[(down.method == method) & (down.config == cfg) & (down.k_selected < down.d)]
    return s.groupby("dataset")[col].mean().reindex(DATASETS).to_numpy()


def acc_raw(method, col="acc_3nn"):
    s = raw[(raw.method == method) & (raw.k_selected < raw.d)]
    return s.groupby("dataset")[col].mean().reindex(DATASETS).to_numpy()


def mean_imp(method, cfg, ds):
    s = imp[(imp.method == method) & (imp.config == cfg) & (imp.dataset == ds)]
    return s.groupby("attribute_j").importance_score.mean()


def rho_bar(pai_cfg, nrs_cfg):
    """Mean Spearman rho between PAI and NRS rankings, and Fisher-z 95% CI
    (weights d-3), as in Section 7.4."""
    r, w, n_undef = [], [], 0
    for ds in DATASETS:
        a, b = mean_imp("pai", pai_cfg, ds), mean_imp("nrs", nrs_cfg, ds)
        rr = stats.spearmanr(a, b).correlation
        n_undef += int(np.isnan(rr))
        r.append(0.0 if np.isnan(rr) else rr)   # constant score vector -> rho = 0
        w.append(len(a) - 3)
    r, w = np.array(r), np.array(w)
    z = np.arctanh(np.clip(r, -0.999, 0.999))
    zb = (w * z).sum() / w.sum()
    se = 1 / np.sqrt(w.sum())
    # Fisher-z weighted mean and its CI (the pair reported in Section 7.4),
    # plus the unweighted mean and the number of undefined correlations.
    return (np.tanh(zb), np.tanh(zb - 1.96 * se), np.tanh(zb + 1.96 * se),
            r.mean(), n_undef)


def wil(x, y):
    d = x - y
    return 1.0 if np.allclose(d, 0) else stats.wilcoxon(x, y).pvalue


def fmt_p(p):
    return r"$<0.001$" if p < 0.001 else f"${p:.3f}$"


rows, notes = [], []
pai_def = acc("pai", "md1_t2.0")
var_null = acc_raw("variance")

# Panel A: NRS neighbourhood size, PAI fixed at its default
for k in NRS_K:
    if not have("nrs", k):
        continue
    n = acc("nrs", k)
    rb, lo, hi, rm, nu = rho_bar("md1_t2.0", k)
    rows.append(("A", f"NRS $k={k[1:]}$" + (" (default)" if k == "k7" else ""),
                 rb, lo, hi, n.mean() * 100, (n - pai_def).mean() * 100,
                 int((n > pai_def).sum()), wil(n, pai_def)))
# Panel B: PAI persistence configuration, NRS fixed at k = 7
nrs7 = acc("nrs", "k7")
for c in PAI_CFG:
    if not have("pai", c):
        continue
    p = acc("pai", c)
    rb, lo, hi, rm, nu = rho_bar(c, "k7")
    print(f"  {c}: unweighted mean rho {rm:+.3f}; undefined rho on {nu} dataset(s)")
    rows.append(("B", PAI_LABEL[c], rb, lo, hi, p.mean() * 100,
                 (nrs7 - p).mean() * 100, int((nrs7 > p).sum()), wil(nrs7, p)))
    notes.append((c, p.mean() * 100, wil(p, var_null), int((p > var_null).sum())))

print(f"{'panel':<5} {'setting':<46} {'rho':>7} {'CI':>17} {'acc':>6} {'NRS-PAI':>8} {'NRS wins':>8} {'p':>7}")
for r in rows:
    print(f"{r[0]:<5} {r[1]:<46} {r[2]:+7.3f} [{r[3]:+.3f},{r[4]:+.3f}] {r[5]:6.1f} {r[6]:+8.2f} {r[7]:>5}/10 {r[8]:7.3f}")
print("\nPAI configurations vs variance null (3-NN):")
for c, a, p, w in notes:
    print(f"  {c:<10} PAI {a:.1f}%  vs variance {var_null.mean()*100:.1f}%  "
          f"PAI wins {w}/10  p={p:.3f}")
print("\nSVM-RBF, NRS - PAI (dataset-level):")
pai_svm = acc("pai", "md1_t2.0", "acc_svm_rbf")
for k in NRS_K:
    if have("nrs", k):
        n = acc("nrs", k, "acc_svm_rbf")
        print(f"  NRS {k}: {n.mean()*100:.1f}% vs PAI {pai_svm.mean()*100:.1f}%  "
              f"wins {(n > pai_svm).sum()}/10  p={wil(n, pai_svm):.3f}")
n7 = acc("nrs", "k7", "acc_svm_rbf")
for c in PAI_CFG:
    if have("pai", c):
        p = acc("pai", c, "acc_svm_rbf")
        print(f"  PAI {c}: {p.mean()*100:.1f}% vs NRS7 {n7.mean()*100:.1f}%  "
              f"NRS wins {(n7 > p).sum()}/10  p={wil(n7, p):.3f}")

# ── LaTeX table ────────────────────────────────────────────────────────────────
body = [r"% AUTO-GENERATED by analyze_ablation.py -- do not edit by hand.",
        r"\begin{surveytable}{1}",
        r"\caption{Sensitivity of the PAI--NRS comparison to the fixed settings.}",
        r"\label{tab:sensitivity}",
        r"\centering\fontsize{8.5}{10.5}\selectfont",
        r"\renewcommand{\arraystretch}{1.12}",
        r"\setlength\tabcolsep{3pt}",
        r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrcrrcr@{}}",
        r"\toprule",
        r"Setting & $\bar\rho_z$ & 95\% CI & Acc.\ (\%) & $\Delta$ (pp) & NRS wins & $p$ \\",
        r"\midrule",
        r"\multicolumn{7}{@{}l}{\textit{(a) NRS neighbourhood size; PAI at its default}} \\"]
for r in rows:
    if r[0] == "B" and r[1] == PAI_LABEL[PAI_CFG[0]]:
        body.append(r"\addlinespace")
        body.append(r"\multicolumn{7}{@{}l}{\textit{(b) PAI persistence setting; NRS at $k=7$}} \\")
    body.append(f"{r[1]} & ${r[2]:+.3f}$ & $[{r[3]:+.2f},\\,{r[4]:+.2f}]$ & "
                f"${r[5]:.1f}$ & ${r[6]:+.2f}$ & {r[7]}/10 & {fmt_p(r[8])} \\\\")
body += [r"\bottomrule", r"\end{tabular*}", r"\par\vspace{4pt}",
         r"{\fontsize{8}{9.5}\selectfont",
         r"\leftskip=0pt\rightskip=0pt plus 1fil\parfillskip=0pt\parindent=0pt",
         r"\textit{Notes.} $\bar\rho_z$: Fisher-$z$ weighted mean (weights $d-3$) of "
         r"the Spearman correlations between PAI and NRS importance on the ten "
         r"datasets, with its 95\% interval; an undefined correlation (constant "
         r"scores) counts as zero.  Acc.: 3-NN accuracy of the varied method, averaged over "
         r"all $k<d$ and then over datasets.  $\Delta$: NRS minus PAI accuracy.  "
         r"$p$: Wilcoxon signed-rank test over the ten dataset-level values.  "
         r"Same subsamples, folds and seeds as Section~\ref{sec:patB}.\par}",
         r"\end{surveytable}"]
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "tab_sensitivity.tex"), "w") as f:
    f.write("\n".join(body) + "\n")
print(f"\nwrote {OUT}/tab_sensitivity.tex")
