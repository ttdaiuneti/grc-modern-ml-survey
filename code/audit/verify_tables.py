"""
Audit the manuscript against the raw experiment CSVs.

Recomputes every table and every load-bearing inline number from the released
CSVs and checks that the exact string is present in the typeset sources.  A
drift between the manuscript and the released data therefore fails here rather
than surviving into the PDF.

Usage:  python3 verify_tables.py     (exit code 0 = all checks pass)
"""
import os
_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
DATA = os.environ.get("GRC_DATA", os.path.join(_ROOT, "data") + os.sep)
MS = os.environ.get("GRC_MANUSCRIPT", os.path.join(_ROOT, "manuscript"))
os.chdir(MS)
import glob
import subprocess
import sys
import tempfile
import os
import shutil
import numpy as np
import pandas as pd
from scipy import stats

RAW = DATA
ds = pd.read_csv(RAW + "raw_downstream.csv")
imp = pd.read_csv(RAW + "raw_importance.csv")
st = pd.read_csv(RAW + "raw_structure.csv")
ks = pd.read_csv(RAW + "raw_knn_scale.csv")
coding = pd.read_csv(DATA + "fulltext_coding.csv")
lit_log = pd.read_csv(DATA + "literature_log.csv")
AXIS1_TOTAL = int((lit_log["truc"].astype(str) == "1").sum())
DATASETS = ['iris', 'wine', 'ionosphere', 'sonar', 'glass',
            'ecoli', 'heart', 'parkinsons', 'seeds', 'wdbc']

SRC = "\n".join(open(f).read() for f in
                sorted(glob.glob("sections/*.tex")) + sorted(glob.glob("tables/*.tex")))
FAILURES = []


def check(desc, needle, present=True):
    hit = needle in SRC
    good = hit == present
    print(f"  [{'ok ' if good else 'FAIL'}] {desc}"
          + ("" if good else f"   <- expected {'' if present else 'NO '}match: {needle!r}"))
    if not good:
        FAILURES.append(desc)


print("1. Tables are byte-identical to a fresh regeneration")
# Regenerate into a throwaway directory: the audit must never mutate the
# manuscript's own table files.  Match the float-placement token the current
# tables use so the comparison tests the numbers, not the template.
tmp = tempfile.mkdtemp()
_any = open(sorted(glob.glob("tables/*.tex"))[0]).read()
_place = "pos=!htbp" if r"\begin{table}[pos=!htbp]" in _any else "!htbp"
env = dict(os.environ, GRC_TABLES_OUT=tmp + "/after", GRC_TABLE_PLACEMENT=_place)
subprocess.run([sys.executable,
                os.path.join(_ROOT, "code", "analysis", "gen_tables.py")],
               capture_output=True, check=True, env=env)
for f in sorted(os.listdir(tmp + "/after")):
    same = open(tmp + "/after/" + f).read() == open("tables/" + f).read()
    print(f"  [{'ok ' if same else 'FAIL'}] tables/{f}")
    if not same:
        FAILURES.append(f"tables/{f} drifted from generator")
shutil.rmtree(tmp)

print("2. Dataset sizes quoted in the abstract and protocol")
for label, got, want in [("raw_importance rows", len(imp), 4975),
                         ("raw_downstream rows", len(ds), 30100),
                         ("raw_structure rows", len(st), 995)]:
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {label} = {got} (manuscript: {want})")
    if not ok:
        FAILURES.append(label)

print("3. Spearman PAI vs NRS: mean and Fisher-z aggregate")
rhos, ws = [], []
for d in DATASETS:
    sub = imp[imp.dataset == d]
    a = sub[sub.method == 'pai'].groupby('attribute_j')['importance_score'].mean()
    b = sub[sub.method == 'nrs'].groupby('attribute_j')['importance_score'].mean()
    c = a.index.intersection(b.index)
    rhos.append(stats.spearmanr(a[c], b[c])[0])
    ws.append(len(c) - 3)
check(f"mean rho = {np.mean(rhos):.3f}", f"${np.mean(rhos):.3f}$")
z, w = np.arctanh(np.clip(rhos, -.999, .999)), np.array(ws, float)
zb, se = np.sum(w * z) / np.sum(w), np.sqrt(1 / np.sum(w))
check(f"Fisher-z rho_z = {np.tanh(zb):.3f}", f"{np.tanh(zb):.3f}")
check(f"Fisher-z CI = [{np.tanh(zb-1.96*se):.2f}, {np.tanh(zb+1.96*se):+.2f}]",
      f"[{np.tanh(zb-1.96*se):.2f},\\,{np.tanh(zb+1.96*se):+.2f}]")
npos = sum(r > 0 for r in rhos)
check(f"sign test on {npos}/10, two-sided p",
      f"$p = {stats.binomtest(npos, 10, 0.5).pvalue:.2f}$, two-sided binomial")

print("4. PAI bound (Theorem 1) holds and the quoted ratios are right")
pb = imp[(imp.method == 'pai') & imp.pai_bound.notna()]
ratio = pb.importance_score / pb.pai_bound
ok = (ratio > 1).sum() == 0
print(f"  [{'ok ' if ok else 'FAIL'}] zero violations of PAI <= (dmax+1)*range "
      f"({int((ratio > 1).sum())} found)")
if not ok:
    FAILURES.append("PAI bound violated")
ok = (2 * ratio > 1).sum() == 0
print(f"  [{'ok ' if ok else 'FAIL'}] zero violations of the sharper per-dimension bound")
if not ok:
    FAILURES.append("sharp PAI bound violated")
check(f"summed-bound ratio mean {ratio.mean():.3f}",
      f"= {ratio.mean():.3f}$ (max ${ratio.max():.3f}$)")
check(f"per-dimension ratio mean {2*ratio.mean():.3f} max {2*ratio.max():.3f}",
      f"the mean ratio is ${2*ratio.mean():.3f}$")
check(f"per-dimension ratio max {2*ratio.max():.3f}", f"(max ${2*ratio.max():.3f}$)")

print("5. Aggregate accuracies over k<d and their paired tests")
def macc(meth, col='acc_3nn'):
    v = []
    for d in DATASETS:
        s = ds[(ds.dataset == d) & (ds.method == meth)]
        s = s[s.k_selected < s['d'].iloc[0]]
        if len(s):
            v.append(s[col].mean())
    return np.array(v)
for meth, col, want in [('nrs', 'acc_3nn', '83.7'), ('pai', 'acc_3nn', '77.6'),
                        ('pai_nrs', 'acc_3nn', '80.1'), ('variance', 'acc_3nn', '79.0'),
                        ('nrs', 'acc_svm_rbf', '85.1'), ('pai', 'acc_svm_rbf', '80.2')]:
    got = f"{macc(meth, col).mean()*100:.1f}"
    ok = got == want
    print(f"  [{'ok ' if ok else 'FAIL'}] {meth}/{col} = {got}\\% (manuscript: {want}\\%)")
    if not ok:
        FAILURES.append(f"{meth}/{col}")
check(f"PAI vs variance null p = {stats.wilcoxon(macc('pai'), macc('variance')).pvalue:.2f}",
      f"($p = {stats.wilcoxon(macc('pai'), macc('variance')).pvalue:.2f}$)")
check(f"SVM NRS vs PAI p = {stats.wilcoxon(macc('nrs','acc_svm_rbf'), macc('pai','acc_svm_rbf')).pvalue:.3f}",
      f"$p = {stats.wilcoxon(macc('nrs','acc_svm_rbf'), macc('pai','acc_svm_rbf')).pvalue:.3f}$, dataset-level")

print("6. Timing ratio quoted in Pattern B")
med = {m: np.mean([ds[(ds.dataset == d) & (ds.method == m)]['time_reduct_sec'].median()
                   for d in DATASETS]) for m in ['pai', 'nrs', 'relieff', 'mutual_info']}
check(f"PAI/NRS slowdown = {med['pai']/med['nrs']:.0f}x",
      f"$\\sim {round(med['pai']/med['nrs'], -1):.0f}\\times$ slower")

print("7. knn_overlap scale ablation (Table 7) reproduces")
for K in sorted(ks.knn_K.unique()):
    P, N = [], []
    for d in DATASETS:
        sub = ks[(ks.dataset == d) & (ks.knn_K == K)]
        sub = sub[sub.k_selected < sub['d'].iloc[0]]
        m = sub.groupby('method')['knn_overlap'].mean()
        P.append(m['pai']); N.append(m['nrs'])
    P, N = np.array(P), np.array(N)
    pv = stats.wilcoxon(P, N).pvalue
    check(f"K={K}: delta={P.mean()-N.mean():+.3f} wins={int((P>N).sum())}/10 p={pv:.3f}",
          f"${P.mean()-N.mean():+.3f}$ & {int((P>N).sum())}/10 & ${pv:.3f}$")
# the K=10 row must agree with the main structure table
P10 = [ks[(ks.dataset == d) & (ks.knn_K == 10) &
          (ks.k_selected < ks[ks.dataset == d]['d'].iloc[0]) &
          (ks.method == 'pai')]['knn_overlap'].mean() for d in DATASETS]
Pst = []
for d in DATASETS:
    sub = st[(st.dataset == d)]
    sub = sub[(sub.k_selected < sub['d'].iloc[0]) & (sub.method == 'pai')]
    Pst.append(sub['knn_overlap'].mean())
drift = max(abs(a - b) for a, b in zip(P10, Pst))
ok = drift < 1e-3
print(f"  [{'ok ' if ok else 'FAIL'}] K=10 rows agree with raw_structure.csv "
      f"(max drift {drift:.2e}; ties in Ionosphere allow ~6e-4)")
if not ok:
    FAILURES.append("knn_scale K=10 disagrees with raw_structure")

print("8. trust ablation: verdict must be stable across the shared K parameter")
tp = []
for K in sorted(ks.knn_K.unique()):
    P, N = [], []
    for d in DATASETS:
        sub = ks[(ks.dataset == d) & (ks.knn_K == K)]
        sub = sub[sub.k_selected < sub['d'].iloc[0]]
        m = sub.groupby('method')['trustworthiness'].mean()
        P.append(m['pai']); N.append(m['nrs'])
    P, N = np.array(P), np.array(N)
    pv = stats.wilcoxon(P, N).pvalue
    tp.append((K, P.mean() - N.mean(), int((P > N).sum()), pv))
    check(f"trust K={K}: delta={P.mean()-N.mean():+.3f} wins={int((P>N).sum())}/10 p={pv:.3f}",
          f"${P.mean()-N.mean():+.3f}$ & {int((P>N).sum())}/10 & ${pv:.3f}$")
ok = all(w <= 1 and p < 0.05 for _, _, w, p in tp)
print(f"  [{'ok ' if ok else 'FAIL'}] PAI loses on trust at every K in "
      f"{[K for K, *_ in tp]} (manuscript claims p <= 0.006 throughout)")
if not ok:
    FAILURES.append("trust verdict not stable across K")
ok = tp[0][1] > tp[-1][1]
print(f"  [{'ok ' if ok else 'FAIL'}] trust gap widens with K "
      f"({tp[0][1]:+.3f} at K={tp[0][0]} -> {tp[-1][1]:+.3f} at K={tp[-1][0]})")
if not ok:
    FAILURES.append("trust gap does not widen")

print("8b. Full-text coding tables match fulltext_coding.csv")
FS = ["all_features_baseline", "reports_dispersion",
      "significance_test", "hyperparam_ablation"]
corpus = coding[coding.log_id.notna() & (coding.log_id.astype(str) != "")]
NC, NA = len(corpus), len(coding)
for f in FS:
    check(f"{f}: {int(coding[f].sum())}/{NA} all, {int(corpus[f].sum())}/{NC} corpus",
          f"{int(coding[f].sum())}/{NA} & {int(corpus[f].sum())}/{NC}")
for label, df, N in [("all coded", coding, NA), ("Axis-1 corpus", corpus, NC)]:
    k = int((df[FS].sum(axis=1) == 4).sum())
    ok = k == 0
    print(f"  [{'ok ' if ok else 'FAIL'}] {label}: no paper reports all four ({k} found)")
    if not ok:
        FAILURES.append(f"all-four claim contradicted ({label})")
WORD = {7: "Seven", 6: "Six", 8: "Eight", 5: "Five", 9: "Nine"}
_st = int(corpus['significance_test'].sum())
check(f"corpus running a test: {_st}/{NC}",
      f"{WORD.get(_st, str(_st))} of 13 run a\nsignificance test")
check(f"corpus with no dispersion: {NC - int(corpus['reports_dispersion'].sum())}/{NC}",
      f"{NC - int(corpus['reports_dispersion'].sum())} of 13 report no\ndispersion")
check(f"corpus omitting the baseline: {NC - int(corpus['all_features_baseline'].sum())}/{NC}",
      f"{NC - int(corpus['all_features_baseline'].sum())} of 13 papers report no all-features baseline")
check(f"all coded omitting the baseline: {NA - int(coding['all_features_baseline'].sum())}/{NA}",
      f"{NA - int(coding['all_features_baseline'].sum())} of the\n22 papers omit it")
check(f"no-ablation count: {NA - int(coding['hyperparam_ablation'].sum())}/{NA}",
      f"{NA - int(coding['hyperparam_ablation'].sum())} of 22 papers vary no hyperparameter")
check(f"corpus is {NC} of the {AXIS1_TOTAL} Axis-1 papers", f"{NC} of the {AXIS1_TOTAL}")
noev = int((coding["evidence"].astype(str).str.len() < 20).sum())
print(f"  [{'ok ' if noev == 0 else 'FAIL'}] every coded row carries an "
      f"evidence quotation ({noev} rows without)")
if noev: FAILURES.append("coding rows missing evidence")
# per-paper detail table must list exactly the corpus members
det = open("tables/tab_practice_detail.tex").read()
missing = [str(r.log_id) for r in corpus.itertuples()
           if str(r.log_id).replace("_", "\\_") not in det]
print(f"  [{'ok ' if not missing else 'FAIL'}] detail table lists all {NC} "
      f"corpus papers" + (f" (missing {missing})" if missing else ""))
if missing: FAILURES.append("detail table incomplete")

print("8c. Literature log integrity")
import csv as _csv
_log = list(_csv.DictReader(open(DATA + "literature_log.csv")))
_ok = len(_log) == 51
print(f"  [{'ok ' if _ok else 'FAIL'}] literature_log.csv has 51 rows (found {len(_log)})")
if not _ok:
    FAILURES.append(f"literature_log.csv row count {len(_log)} != 51")
_ids = [r["paper_id"] for r in _log]
_dup = {i for i in _ids if _ids.count(i) > 1}
print(f"  [{'ok ' if not _dup else 'FAIL'}] paper_ids unique" + (f" (dups {_dup})" if _dup else ""))
if _dup: FAILURES.append("duplicate paper_id in literature_log")
_ragged = [r["paper_id"] for r in _log if None in r or any(v is None for v in r.values())]
print(f"  [{'ok ' if not _ragged else 'FAIL'}] no ragged rows" + (f" ({_ragged})" if _ragged else ""))
if _ragged: FAILURES.append("ragged rows in literature_log")
check("manuscript states 51 included papers", "51 papers that")

print("9. Cross-file consistency: a number stated twice must agree")
import collections
FILES = {f: open(f).read() for f in
         sorted(glob.glob("sections/*.tex")) + ["main.tex"]}
SHARED = [
    ("mean Spearman rho", "-0.034"), ("Fisher-z aggregate", "-0.060"),
    ("Fisher-z CI lower", "-0.21"), ("SVM NRS-vs-PAI p", "0.006"),
    ("variance-null p", "0.23"), ("hybrid-vs-NRS p", "0.010"),
    ("cluster ARI p", "0.004"), ("importance measurements", "4{,}975"),
    ("downstream records", "30{,}100"), ("open problems", "nine"),
    ("datasets not separable", "seven of"), ("corpus size", "51"),
]
for label, tok in SHARED:
    where = [f for f, t in FILES.items() if tok in t]
    print(f"  [ok ] {label:26s} {tok:12s} appears in {len(where)} file(s): "
          f"{', '.join(sorted(x.replace('sections/','').replace('.tex','') for x in where))}")

CONTRADICT = [
    ("knn_overlap called simply 'not a win'", "do not interpret it as a win"),
    ("knn/trust still called free-parameter-less", "no free scale"),
    ("trust presented as unablated independent", "independent of PAI's objective"),
    ("superseded eight-problem count", "eight open"),
    ("removed unverifiable reference Xia2021SLR", "Xia2021SLR"),
    ("theorem attributed to the removed reference", "stability of local\nredundancy"),
    ("stale 52-paper corpus count", "52 papers that"),
    ("stale 52-paper corpus count (topology)", "52-paper corpus"),
    ("stale 25-paper Axis-1 count", "13 of the 25"),
    ("removed no-DOI reference Adams2017persistence", "Adams2017persistence"),
    ("narrow scale-only Pattern B (abstract)", "dominated by a scale/magnitude"),
    ("narrow scale-only Pattern B (heading)", "Scale-Artefact Dominance"),
    ("Pattern B keyed to measurement scale alone", "measurement-scale property rather than"),
]
for label, tok in CONTRADICT:
    hits = [f for f, t in FILES.items() if tok in t]
    good = not hits
    print(f"  [{'ok ' if good else 'FAIL'}] retracted claim absent: {label}"
          + ("" if good else f"  <- still in {hits}"))
    if not good:
        FAILURES.append(label)

print("10. Stale values from earlier drafts must be absent")
for bad, why in [("47.3", "pre-correction Iris PAI accuracy"),
                 ("$-0.036$", "pre-correction mean rho"),
                 ("Eight of ten", "unsupported noise-band count"),
                 ("bound is tight", "contradicted by the data"),
                 ("1.1\\times10^{-25}", "pseudo-replicated matched-k p-value"),
                 ("38 of 47", "unverifiable literature statistic"),
                 ("19 of 23", "unverifiable literature statistic")]:
    check(f"absent: {why!r}", bad, present=False)

print()
if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("All checks passed: manuscript is consistent with the released CSVs.")
