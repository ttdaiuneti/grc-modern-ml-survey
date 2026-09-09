"""
Regenerate every data table in the manuscript from the raw experiment CSVs.

Single source of truth: the CSVs under E1-experiments/.  Each table is written
to tables/<label>.tex and \input by the section that displays it, so no number
is ever hand-transcribed.  Run verify_tables.py afterwards to audit.
"""
import os
DATA = os.environ.get("GRC_DATA",
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "..", "data") + os.sep)
import os
import re
import numpy as np
import pandas as pd
from scipy import stats

RAW = DATA
ds = pd.read_csv(RAW + "raw_downstream.csv")
kscale = pd.read_csv(RAW + "raw_knn_scale.csv")
coding = pd.read_csv(DATA + "fulltext_coding.csv")
imp = pd.read_csv(RAW + "raw_importance.csv")
st = pd.read_csv(RAW + "raw_structure.csv")

DATASETS = ['iris', 'wine', 'ionosphere', 'sonar', 'glass',
            'ecoli', 'heart', 'parkinsons', 'seeds', 'wdbc']
NAME = {'iris': 'Iris', 'wine': 'Wine', 'ionosphere': 'Ionosphere',
        'sonar': 'Sonar', 'glass': 'Glass', 'ecoli': 'Ecoli',
        'heart': 'Heart', 'parkinsons': 'Parkinsons', 'seeds': 'Seeds',
        'wdbc': 'WDBC'}

# Where to write the .tex files (verify_tables.py points this at a temp dir so
# an audit never mutates the manuscript).
OUT = os.environ.get("GRC_TABLES_OUT", "tables")
# Float placement: "!htbp" for the Springer sn-jnl build, "pos=!htbp" for the
# Elsevier CAS build.  Set GRC_TABLE_PLACEMENT to override.
PLACEMENT = os.environ.get("GRC_TABLE_PLACEMENT", "!htbp")
# Layout style.  "elsevier" (default): a plain \begin{table} with \small and a
# long descriptive caption -- the Elsevier CAS manuscript in paper/.  "springer":
# the compact \begin{surveytable} wrapper used by the Artificial Intelligence
# Review submission in AIR/ -- a short caption plus a separate footnotesize
# "Notes." block carrying the same descriptive text.  The data rows are byte
# identical between the two; only the wrapper, font and caption/notes split
# differ.  Set GRC_TABLE_STYLE=springer to emit the AIR layout.
STYLE = os.environ.get("GRC_TABLE_STYLE", "elsevier")

# Short captions for the Springer layout, keyed by \label.  The long caption
# emitted below becomes the "Notes." text unless overridden in SPRINGER_NOTES.
SPRINGER_CAPTION = {
    "tab:allfeats": "Best-subset versus all-features 3-NN accuracy.",
    "tab:rho": "Agreement between PAI and NRS importance rankings.",
    "tab:pai_range": "Association between PAI importance and feature range.",
    "tab:structure": "Structure preservation: PAI versus NRS.",
    "tab:iris_top": "Top-ranked attributes and single-feature accuracy on Iris.",
    "tab:knn_scale": "Sensitivity of local structure metrics to neighbourhood size.",
    "tab:practice": "Reporting practices in the full-text sample.",
    "tab:practice_detail": "Per-paper reporting-practice coding for the Axis-1 corpus.",
}
SPRINGER_NOTES = {
    "tab:iris_top": ("Iris: $n=150$, $d=4$. Each attribute maximises mean\n"
                     "importance over five seed subsamples. Accuracy is mean "
                     "$\\pm$ SD over\n25 cross-validation runs (5 folds $\\times$ "
                     "5 seeds), using that attribute only."),
}

os.makedirs(OUT, exist_ok=True)


def _slice_caption(body):
    """Return (caption_text, rest_without_caption_line) from a generated body."""
    i = body.index(r"\caption{") + len(r"\caption{")
    depth = 1
    j = i
    while depth:
        if body[j] == "{":
            depth += 1
        elif body[j] == "}":
            depth -= 1
        j += 1
    return body[i:j - 1]


def _to_springer(label, body):
    """Rewrite an Elsevier \\begin{table} body into the AIR surveytable layout."""
    caption = _slice_caption(body)
    notes = SPRINGER_NOTES.get(label, caption)
    short = SPRINGER_CAPTION[label]
    colspec = re.search(r"\\begin\{tabular\}\{([^}]*)\}", body).group(1)
    rows = body.split("\\begin{tabular}{" + colspec + "}\n", 1)[1]
    rows = rows.split("\n\\end{tabular}", 1)[0]
    tabcolsep = re.search(r"\n(\\setlength\\tabcolsep\{[^}]*\})\n", body)
    out = [r"\begin{surveytable}{1}",
           r"\caption{" + short + "}",
           r"\label{" + label + "}",
           r"\centering\fontsize{8.5}{10.5}\selectfont",
           r"\renewcommand{\arraystretch}{1.12}"]
    if tabcolsep:
        out.append(tabcolsep.group(1))
    out.append(r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}"
               + colspec + r"@{}}")
    out.append(rows)
    out += [r"\end{tabular*}",
            r"\par\vspace{4pt}",
            r"{\fontsize{8}{9.5}\selectfont",
            r"\leftskip=0pt\rightskip=0pt plus 1fil\parfillskip=0pt\parindent=0pt",
            r"\textit{Notes.} " + notes + r"\par}",
            r"\end{surveytable}"]
    return "\n".join(out)


def holm(pvals):
    """Holm step-down adjusted p-values, preserving input order."""
    order, prev, out = np.argsort(pvals), 0.0, [0.0] * len(pvals)
    for rank, i in enumerate(order):
        prev = min(1.0, max(prev, (len(pvals) - rank) * pvals[i]))
        out[i] = prev
    return out


def write(label, body):
    tex_label = re.search(r"\\label\{([^}]*)\}", body).group(1)
    if STYLE == "springer":
        header = ("% AUTO-GENERATED by gen_tables.py (GRC_TABLE_STYLE=springer)"
                  " -- do not edit by hand.\n"
                  "% Regenerate:  GRC_TABLE_STYLE=springer python3 gen_tables.py"
                  "   Audit:  python3 verify_tables.py\n")
        body = _to_springer(tex_label, body)
    else:
        header = ("% AUTO-GENERATED by gen_tables.py -- do not edit by hand.\n"
                  "% Regenerate:  python3 gen_tables.py"
                  "   Audit:  python3 verify_tables.py\n")
        body = body.replace(r"\begin{table}[!htbp]",
                            r"\begin{table}[" + PLACEMENT + "]")
    with open(f"{OUT}/{label}.tex", "w") as f:
        f.write(header)
        f.write(body.rstrip() + "\n")
    print(f"  wrote {OUT}/{label}.tex")


# ── tab:allfeats — best-k vs all-features, with paired test ──────────────────
rows, praw = [], []
for d in DATASETS:
    sub = ds[ds.dataset == d]
    allf = sub[sub.method == 'all_features'].set_index(['seed', 'fold'])['acc_3nn']
    per = sub.groupby(['method', 'k_selected'])['acc_3nn'].mean()
    bi = per.idxmax()
    best = sub[(sub.method == bi[0]) & (sub.k_selected == bi[1])] \
        .set_index(['seed', 'fold'])['acc_3nn']
    j = best.index.intersection(allf.index)
    diff = best[j] - allf[j]
    praw.append(1.0 if diff.abs().sum() == 0
                else stats.wilcoxon(best[j], allf[j]).pvalue)
    rows.append(dict(name=NAME[d], n=int(sub.n.iloc[0]), d=int(sub.d.iloc[0]),
                     am=allf[j].mean() * 100, asd=allf[j].std(ddof=1) * 100,
                     bm=best[j].mean() * 100, bsd=best[j].std(ddof=1) * 100,
                     k=int(bi[1]), delta=diff.mean() * 100))

body = [r"""\begin{table}[!htbp]
\caption{Best-$k$ 3-NN accuracy (maximised over methods and
$k \in \{1,\ldots,d\}$) versus all-features baseline.  Mean $\pm$ SD over
5~folds $\times$ 5~seeds.  $\Delta$ is the margin in percentage points;
$p_{\mathrm{Holm}}$ is a paired Wilcoxon signed-rank test over the 25
matched fold--seed pairs, Holm-corrected for the ten comparisons.
$\dagger$ marks the dataset where best-$k = d$, i.e.\ no strict subset
strictly outperforms the full feature set (on Heart the maximum is an exact
tie among several methods, one of which is the full set).}
\label{tab:allfeats}
\centering\small
\setlength\tabcolsep{4pt}
\begin{tabular}{lrrccrrr}
\toprule
Dataset & $n$ & $d$ & All-feat acc. & Best-$k$ acc. & $k^*$ & $\Delta$ (pp) & $p_{\mathrm{Holm}}$ \\
\midrule"""]
for r, ph in zip(rows, holm(praw)):
    dag = r"$\dagger$" if r['k'] == r['d'] else ""
    ps = r"$<0.001$" if ph < 0.001 else f"${ph:.3f}$"
    body.append(f"{r['name']:11s}& {r['n']:3d} & {r['d']:2d} & "
                f"${r['am']:.1f} \\pm {r['asd']:.1f}$\\% & "
                f"${r['bm']:.1f} \\pm {r['bsd']:.1f}$\\% & "
                f"{r['k']}{dag} & ${r['delta']:+.2f}$ & {ps} \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_allfeats", "\n".join(body))

# ── tab:rho — Spearman PAI vs NRS ───────────────────────────────────────────
body = [r"""\begin{table}[!htbp]
\caption{Spearman $\rho$ between PAI and NRS importance rankings per dataset
(mean importance over 5 seeds before ranking; $d$ = number of attributes,
which is also the sample size for the Spearman test).
Note: datasets with $d \leq 7$ cannot reach $p < 0.05$ at any $\rho$.}
\label{tab:rho}
\centering\small
\begin{tabular}{lccc}
\toprule
Dataset & $d$ & $\rho$ & $p$-value \\
\midrule"""]
rhos = []
for d in DATASETS:
    sub = imp[imp.dataset == d]
    a = sub[sub.method == 'pai'].groupby('attribute_j')['importance_score'].mean()
    b = sub[sub.method == 'nrs'].groupby('attribute_j')['importance_score'].mean()
    c = a.index.intersection(b.index)
    r, pv = stats.spearmanr(a[c], b[c])
    rhos.append(r)
    body.append(f"{NAME[d]:11s}& {len(c):2d} & ${r:+.2f}$ & ${pv:.2f}$ \\\\")
body.append(r"\midrule")
body.append(f"Mean (10)  & --- & ${np.mean(rhos):.3f}$ & --- \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_rho", "\n".join(body))

# ── tab:pai_range — Spearman PAI vs range ───────────────────────────────────
body = [r"""\begin{table}[!htbp]
\caption{Spearman $\rho$ between mean PAI score and
$\mathrm{range}(a_j)$ per dataset.  Data is z-score standardised,
so range variation across features reflects kurtosis and outlier
structure, not raw measurement scale.}
\label{tab:pai_range}
\centering\small
\begin{tabular}{lccc}
\toprule
Dataset & $d$ & $\rho(\text{PAI},\text{range})$ & $p$ \\
\midrule"""]
prs = []
for d in DATASETS:
    g = imp[(imp.dataset == d) & (imp.method == 'pai')].groupby('attribute_j').agg(
        pai=('importance_score', 'mean'), rng=('pai_bound', 'mean'))
    r, pv = stats.spearmanr(g.pai, g.rng)
    prs.append(r)
    ps = r"$<0.001$" if pv < 0.001 else f"${pv:.3f}$"
    body.append(f"{NAME[d]:11s}& {len(g):2d} & ${r:+.2f}$ & {ps} \\\\")
body.append(r"\midrule")
body.append(f"Mean (10)  & --- & ${np.mean(prs):+.2f}$ & --- \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_pai_range", "\n".join(body))

# ── tab:structure — structure preservation, all columns over k<d ────────────
body = [r"""\begin{table}[!htbp]
\caption{Structure-preservation comparison, PAI vs NRS (10 datasets).
\texttt{wass\_persist} is lower-is-better (PAI's own metric); the others are
higher-is-better and are not algebraically tied to PAI's objective.  Note that
\texttt{trust} and \texttt{knn\_overlap} share a neighbourhood-size parameter,
fixed here at the conventional $K=10$ and ablated in
Table~\ref{tab:knn_scale}.  Means, SDs, win counts
and tests all use the same aggregation: one value per dataset, averaged over
$k<d$.  $p$-values: dataset-level paired Wilcoxon signed-rank
($n=10$, two-sided).}
\label{tab:structure}
\centering\small
\begin{tabular}{lcccc}
\toprule
Metric & PAI (mean $\pm$ SD) & NRS (mean $\pm$ SD) & PAI wins / 10 & $p$ \\
\midrule"""]
LABEL = {'wass_persist': r'\texttt{wass\_persist}',
         'knn_overlap': r'\texttt{knn\_overlap}',
         'trustworthiness': r'\texttt{trust}',
         'cluster_ari': r'\texttt{cluster\_ari}'}
for metric, lower_better, fmt in [('wass_persist', True, '.1f'),
                                  ('knn_overlap', False, '.3f'),
                                  ('trustworthiness', False, '.3f'),
                                  ('cluster_ari', False, '.3f')]:
    P, N = [], []
    for d in DATASETS:
        sub = st[st.dataset == d]
        sub = sub[sub.k_selected < sub['d'].iloc[0]]
        m = sub.groupby('method')[metric].mean()
        if 'pai' in m and 'nrs' in m:
            P.append(m['pai']); N.append(m['nrs'])
    P, N = np.array(P), np.array(N)
    wins = int(np.sum(P < N) if lower_better else np.sum(P > N))
    pv = stats.wilcoxon(P, N).pvalue
    body.append(f"{LABEL[metric]:24s}& ${P.mean():{fmt}} \\pm {P.std(ddof=1):{fmt}}$ "
                f"& ${N.mean():{fmt}} \\pm {N.std(ddof=1):{fmt}}$ "
                f"& {wins}/10 & ${pv:.3f}$ \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_structure", "\n".join(body))

# ── tab:iris_top ────────────────────────────────────────────────────────────
ATTR = {0: r'\texttt{sepal\_length}', 1: r'\texttt{sepal\_width}',
        2: r'\texttt{petal\_length}', 3: r'\texttt{petal\_width}'}
body = [r"""\begin{table}[!htbp]
\caption{Top-ranked attribute by method on Iris ($n=150$, $d=4$).  The
top-1 attribute is the arg-max of mean importance over the five seed
subsamples; the accuracies are mean $\pm$ SD over the 25 cross-validation
runs (5 folds $\times$ 5 seeds) using only that attribute. PAI
selects the attribute whose removal most disrupts the persistence diagram;
NRS selects the most discriminative attribute for the class label.}
\label{tab:iris_top}
\centering\small
\begin{tabular}{lccc}
\toprule
Method & Top-1 attribute & 3-NN acc.\ (top-1) & SVM acc.\ (top-1) \\
\midrule"""]
for m, lab in [('pai', 'PAI'), ('nrs', 'NRS')]:
    top = int(imp[(imp.dataset == 'iris') & (imp.method == m)]
              .groupby('attribute_j')['importance_score'].mean().idxmax())
    sub = ds[(ds.dataset == 'iris') & (ds.method == m) & (ds.k_selected == 1)]
    body.append(f"{lab}  & {ATTR[top]}  & "
                f"${sub.acc_3nn.mean()*100:.1f} \\pm {sub.acc_3nn.std(ddof=1)*100:.1f}$\\% & "
                f"${sub.acc_svm_rbf.mean()*100:.1f} \\pm {sub.acc_svm_rbf.std(ddof=1)*100:.1f}$\\% \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_iris_top", "\n".join(body))

# ── tab:knn_scale — both K-parameterised metrics, ablated on the same grid ──
body = [r"""\begin{table}[!htbp]
\caption{Ablation of the neighbourhood parameter $K$ shared by the two
local structure metrics.  Feature subsets are exactly those of
Table~\ref{tab:structure}; only $K$ changes.  Each row aggregates over $k<d$
per dataset, then compares PAI with NRS by dataset-level paired Wilcoxon
signed-rank ($n=10$, two-sided); $\Delta = \mathrm{PAI}-\mathrm{NRS}$, and
$^{*}$ marks $p<0.05$.  $K=10$ is the default used in
Table~\ref{tab:structure} and throughout the literature.}
\label{tab:knn_scale}
\centering\small
\begin{tabular}{ccccc}
\toprule
$K$ & PAI & NRS & $\Delta$ & PAI wins / 10 & $p$ \\
\midrule
\multicolumn{6}{l}{\emph{\texttt{knn\_overlap}} (higher is better)} \\"""]
body[0] = body[0].replace(r"\begin{tabular}{ccccc}", r"\begin{tabular}{cccccc}")


def panel(metric):
    out = []
    for K in sorted(kscale.knn_K.unique()):
        P, N = [], []
        for d in DATASETS:
            sub = kscale[(kscale.dataset == d) & (kscale.knn_K == K)]
            sub = sub[sub.k_selected < sub['d'].iloc[0]]
            m = sub.groupby('method')[metric].mean()
            P.append(m['pai']); N.append(m['nrs'])
        P, N = np.array(P), np.array(N)
        if np.isnan(P).any():
            continue
        pv = stats.wilcoxon(P, N).pvalue
        mark = r"\,$^{*}$" if pv < 0.05 else ""
        out.append(f"{K:2d} & ${P.mean():.3f}$ & ${N.mean():.3f}$ & "
                   f"${P.mean()-N.mean():+.3f}$ & {int((P>N).sum())}/10 & "
                   f"${pv:.3f}${mark} \\\\")
    return out


body += panel("knn_overlap")
body.append(r"\addlinespace")
body.append(r"\multicolumn{6}{l}{\emph{\texttt{trust}} (higher is better)} \\")
body += panel("trustworthiness")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_knn_scale", "\n".join(body))

# ── tab:practice — reporting practice, aggregate ────────────────────────────
FIELDS = [("all_features_baseline", "All-features baseline reported"),
          ("reports_dispersion",    "Dispersion (SD or per-fold) reported"),
          ("significance_test",     "Statistical significance test run"),
          ("hyperparam_ablation",   "Own hyperparameter ablated")]
FN = [f for f, _ in FIELDS]

lit_log = pd.read_csv(DATA + "literature_log.csv")
AXIS1_TOTAL = int((lit_log["truc"] == "1").sum())
corpus = coding[coding.log_id.notna() & (coding.log_id.astype(str) != "")]
N, NC = len(coding), len(corpus)
body = [r"""\begin{table}[!htbp]
\caption{Reporting practice in attribute-reduction papers read at full text.
Each cell is a presence/absence judgement made from the experimental section
only; the coding and the supporting quotation for every cell are released as
\texttt{fulltext\_coding.csv}.  Column~2 covers all """ + str(N) + r""" papers
coded; column~3 restricts to the """ + str(NC) + r""" that are members of this
survey's Axis-1 corpus (Appendix~\ref{app:search}), i.e.\ """ + str(NC) + r"""
of the """ + str(AXIS1_TOTAL) + r""" Axis-1 papers.}
\label{tab:practice}
\centering\small
\begin{tabular}{lcc}
\toprule
Practice & All coded ($n=""" + str(N) + r"""$) & Axis-1 corpus ($n=""" + str(NC) + r"""$) \\
\midrule"""]
for f, label in FIELDS:
    a, b = int(coding[f].sum()), int(corpus[f].sum())
    body.append(f"{label} & {a}/{N} & {b}/{NC} \\\\")
body.append(r"\midrule")
body.append(f"\\textbf{{All four}} & {int((coding[FN].sum(axis=1)==4).sum())}/{N} & "
            f"{int((corpus[FN].sum(axis=1)==4).sum())}/{NC} \\\\")
body.append(f"\\textbf{{None of the four}} & {int((coding[FN].sum(axis=1)==0).sum())}/{N} & "
            f"{int((corpus[FN].sum(axis=1)==0).sum())}/{NC} \\\\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_practice", "\n".join(body))

# ── tab:practice_detail — per-paper, corpus members (appendix) ──────────────
body = [r"""\begin{table}[!htbp]
\caption{Per-paper coding for the """ + str(NC) + r""" Axis-1 corpus papers read at
full text.  B~= all-features baseline; D~= dispersion; S~= significance test;
A~= own-hyperparameter ablation.  $\bullet$~= present, --~= absent.  The
quotation supporting each judgement is in \texttt{fulltext\_coding.csv}.}
\label{tab:practice_detail}
\centering\small
\begin{tabular}{llcccc}
\toprule
Log ID & Paper & B & D & S & A \\
\midrule"""]
mark = lambda v: r"$\bullet$" if int(v) else "--"
for r_ in corpus.sort_values("log_id").itertuples():
    name = f"{r_.first_author} {r_.year}"
    body.append(f"{str(r_.log_id).replace(chr(95), chr(92)+chr(95))} & {name} & " +
                " & ".join(mark(getattr(r_, f)) for f in FN) + r" \\")
body.append("\\bottomrule\n\\end{tabular}\n\\end{table}")
write("tab_practice_detail", "\n".join(body))

print("\nAll tables regenerated from raw CSVs.")
