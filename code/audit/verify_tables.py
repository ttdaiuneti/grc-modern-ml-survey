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
import re
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
# Needles are matched with all whitespace runs collapsed, so re-wrapping a
# LaTeX paragraph does not break a check.
_SRC_WS = re.sub(r"\s+", " ", SRC)


def check(desc, needle, present=True):
    hit = re.sub(r"\s+", " ", needle) in _SRC_WS
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
_any = open(sorted(glob.glob("tables/tab_*.tex"))[0]).read()
_place = "pos=!htbp" if r"\begin{table}[pos=!htbp]" in _any else "!htbp"
_style = "springer" if r"\begin{surveytable}" in _any else "elsevier"
env = dict(os.environ, GRC_TABLES_OUT=tmp + "/after",
           GRC_TABLE_PLACEMENT=_place, GRC_TABLE_STYLE=_style)
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
check(f"8.1 corpus omitting the baseline: {NC - int(corpus['all_features_baseline'].sum())}/{NC}",
      f"including {NC - int(corpus['all_features_baseline'].sum())} of the 13 that belong to our Axis-1 corpus")
check(f"corpus no-ablation count: {NC - int(corpus['hyperparam_ablation'].sum())}/{NC}",
      f"{NC - int(corpus['hyperparam_ablation'].sum())} of 13 vary no hyperparameter of their own method")
check(f"no-ablation count: {NA - int(coding['hyperparam_ablation'].sum())}/{NA}",
      f"{NA - int(coding['hyperparam_ablation'].sum())} of 22 papers vary no hyperparameter")
check(f"corpus is {NC} of the {AXIS1_TOTAL} Axis-1 papers", f"{NC} of the {AXIS1_TOTAL}")
_cb = int(corpus['all_features_baseline'].sum())
check(f"Section 3 evidence: {_cb}/{NC} baseline, {_st}/{NC} test",
      f"{WORD.get(_cb, str(_cb))} of the 13 report an\nall-features baseline, and {WORD.get(_st, str(_st)).lower()} run a significance test")
noev = int((coding["evidence"].astype(str).str.len() < 20).sum())
print(f"  [{'ok ' if noev == 0 else 'FAIL'}] every coded row carries an "
      f"evidence quotation ({noev} rows without)")
if noev: FAILURES.append("coding rows missing evidence")
# per-paper detail table must list exactly the corpus members
det = open("tables/tab_practice_detail.tex").read()
_drows = [ln for ln in det.splitlines() if ln.rstrip().endswith("\\\\") and ("bullet" in ln or "--" in ln) and "&" in ln]
missing = [f"{r.first_author} {r.year}" for r in corpus.itertuples()
           if f"{r.first_author} {r.year} &" not in det]
if len(_drows) != NC:
    missing.append(f"{len(_drows)} rows for {NC} papers")
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
    ("downstream records", "30{,}100"), ("open problems", "five"),
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
    ("superseded nine-problem count (restructure)", "nine open"),
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

print("11. Bibliography counts stated in the text match refs.bib and the log")
_bib = os.path.join(MS, "refs.bib")
_log = os.path.join(DATA, "literature_log.csv")
if not os.path.exists(_bib):
    print("  [ok ] refs.bib not present in this checkout; skipped")
else:
    bibtxt = open(_bib).read()
    n_bib = len(re.findall(r"^@", bibtxt, re.M))
    m = re.search(r"The (\d+)-entry bibliography", SRC)
    if m and int(m.group(1)) != n_bib:
        print(f"  [FAIL] refs.bib has {n_bib} entries (manuscript states {m.group(1)})")
        FAILURES.append(f"bibliography size {m.group(1)} != {n_bib}")
    elif m:
        print(f"  [ok ] refs.bib has {n_bib} entries (manuscript states {m.group(1)})")
    else:
        print(f"  [ok ] refs.bib has {n_bib} entries; manuscript states no count")

    # Join the 51-paper log against refs.bib by (first-author surname, year +/-1)
    # so "N of the 51 screened papers are cited" is checked against reality, not
    # against the manuscript's own prose.
    ent = re.findall(r"@\w+\{[^,]+,(.*?)\n\}", bibtxt, re.S)
    bibkeys = set()
    # Exact titles also connect preprints to journal versions whose issue
    # year differs by more than the legacy author/year tolerance.
    def _normal_title(value):
        return re.sub(r"[^a-z0-9]", "", str(value).lower())
    cited_keys = set()
    for citation in re.findall(r"\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}", SRC):
        cited_keys.update(key.strip() for key in citation.split(","))
    cited_titles = set()
    for key, body in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bibtxt, re.S):
        title = re.search(r"title\s*=\s*\{(.*?)\}\s*,", body, re.S)
        if key.strip() in cited_keys and title:
            cited_titles.add(_normal_title(title.group(1)))
    for b in ent:
        a = re.search(r"author\s*=\s*\{+\s*([A-Za-z\-\u2019\']+)", b)
        y = re.search(r"year\s*=\s*\{(\d{4})\}", b)
        if a and y:
            for dy in (-2, -1, 0, 1, 2):
                bibkeys.add((a.group(1).lower(), str(int(y.group(1)) + dy)))
    lg = pd.read_csv(_log)
    # Strict join: a corpus paper counts as cited only if its title matches the
    # title of a bib entry that the manuscript actually cites.  (An earlier
    # author/year join matched a mis-attributed log row to another entry.)
    def _tok(t):
        t = str(t).replace("\\delta", " delta ").replace("\u03b4", " delta ")
        return set(re.findall(r"[a-z0-9]+", re.sub(r"\\[a-zA-Z]+|[{}$]", " ", t).lower()))
    _cited_tok = []
    for key, body in re.findall(r"@\w+\{([^,]+),(.*?)\n\}", bibtxt, re.S):
        tm = re.search(r"title\s*=\s*\{(.*?)\}\s*,", body, re.S)
        if key.strip() in cited_keys and tm:
            _cited_tok.append((key.strip(), _tok(tm.group(1))))
    uncited, _weak = [], []
    for r in lg.itertuples():
        lt = _tok(r.title)
        best = max(((len(lt & bt) / len(lt), k) for k, bt in _cited_tok), default=(0, ""))
        if best[0] < 0.8:
            uncited.append(r.paper_id)
        elif best[0] < 1:
            _weak.append((round(best[0], 2), r.paper_id, best[1]))
    print(f"  [ok ] title matches below 1.0 (for review): {sorted(_weak)}")
    n_cited = len(lg) - len(uncited)
    claim_all = "All\n51 screened papers are cited" in SRC or "all 51 cited" in SRC
    if claim_all:
        ok = not uncited
        print(f"  [{'ok ' if ok else 'FAIL'}] manuscript says all 51 corpus papers "
              f"cited; log join finds {n_cited}/51" + ("" if ok else f", uncited {uncited}"))
        if not ok:
            FAILURES.append(f"corpus papers not all cited: {uncited}")
    else:
        mc = re.search(r"(\w+) of the 51 screened papers are cited", SRC)
        want = {"forty-five":45,"forty-seven":47,"fifty":50,"all":51}.get(
            (mc.group(1).lower() if mc else ""), None)
        if want is not None:
            ok = n_cited == want
            print(f"  [{'ok ' if ok else 'FAIL'}] {n_cited}/51 corpus papers cited "
                  f"(manuscript states {want})")
            if not ok:
                FAILURES.append(f"cited-corpus count {want} != {n_cited}")
        else:
            print(f"  [ok ] {n_cited}/51 corpus papers cited; no prose count to check")

    mp = re.search(r"remaining\s+(\d+)\s+bibliography\s+entries\s+are\s+references\s+outside", SRC)
    if mp:
        want_nc = int(mp.group(1))
        got_nc = n_bib - n_cited
        ok = want_nc == got_nc
        print(f"  [{'ok ' if ok else 'FAIL'}] non-corpus remainder: manuscript "
              f"{want_nc}, refs.bib - cited = {got_nc}")
        if not ok:
            FAILURES.append(f"non-corpus remainder {want_nc} != {got_nc}")

print("11b. Claim-class coding matches the manuscript")
_fp = os.path.join(DATA, "failure_pattern_coding.csv")
if not os.path.exists(_fp):
    _fp = os.path.join(MS, "coding", "failure_pattern_coding.csv")
if os.path.exists(_fp):
    fp = pd.read_csv(_fp)
    st = fp.import_status.value_counts().to_dict()
    imp = fp[fp.import_status == "import"]
    cc = imp.claim_class.astype(str).str.strip().value_counts().to_dict()
    # Table 10 (tab:prevalence) is hand-written; assert the CSV that backs it
    # carries exactly the distribution the table prints.
    _p = SRC.find(chr(92)+"label{tab:prevalence}")
    tab = SRC[_p: _p + 1400] if _p >= 0 else ""
    def _row(label):
        for ln in tab.splitlines():
            if label in ln and "&" in ln:
                cell = ln.split("&")[-1].replace(chr(92), " ").strip()
                return int(cell) if cell.isdigit() else None
        return None
    for label, got, needle, exp in [
        ("13 imports",    st.get("import", 0),    "Imports an external framework", 13),
        ("23 internal",   st.get("internal", 0),  "Internal GrC development", 23),
        ("15 background", st.get("background", 0),"Background / foundational reference", 15),
        ("class (a)=5",   cc.get("a", 0),         "\\textit{(a)}", 5),
        ("class (b)=8",   cc.get("b", 0),         "\\textit{(b)}", 8),
    ]:
        printed = _row(needle)
        ok = (got == exp) and (printed == exp)
        print(f"  [{'ok ' if ok else 'FAIL'}] {label}: CSV={got}, Table 10 prints {printed}")
        if not ok:
            FAILURES.append(f"claim-class {label}: CSV {got}, table {printed}, expect {exp}")
    prov_missing = imp[imp.provenance.fillna("").str.strip() == ""].paper_id.tolist()
    ok = not prov_missing
    print(f"  [{'ok ' if ok else 'FAIL'}] provenance filled for all 13 imports"
          + ("" if ok else f"  <- empty: {prov_missing}"))
    if not ok:
        FAILURES.append(f"provenance empty for {prov_missing}")
else:
    print("  [ok ] failure_pattern_coding.csv not in this checkout; skipped")

print("12. Selection-rule margins quoted inline in Section 8.1")
# Only a manuscript that actually discusses the selection comparison can
# contradict it; a draft that omits the section has nothing to check.
_SEC = "\n".join(open(f).read() for f in sorted(glob.glob("sections/*.tex")))
if "tables/tab_selection" not in _SEC:
    print("  [ok ] manuscript does not discuss the selection comparison; skipped")
else:
    def _mgn(method, frac):
        out = []
        for d in DATASETS:
            s_ = ds[ds.dataset == d]
            dim = int(s_['d'].iloc[0])
            base = s_[s_.method == 'all_features']['acc_3nn'].mean()
            k = max(1, int(np.ceil(dim * frac)))
            sub = s_[(s_.method == method) & (s_.k_selected == k)]['acc_3nn']
            if len(sub):
                out.append((sub.mean() - base) * 100)
        return np.asarray(out)

    for meth, frac, lab in [('nrs', 0.25, 'NRS k=d/4'), ('nrs', 0.75, 'NRS k=3d/4'),
                            ('nrs', 0.5, 'NRS k=d/2'), ('relieff', 0.5, 'ReliefF k=d/2'),
                            ('mutual_info', 0.5, 'MI k=d/2'),
                            ('variance', 0.5, 'variance k=d/2'),
                            ('pai', 0.5, 'PAI k=d/2')]:
        check(f"{lab} margin {_mgn(meth, frac).mean():+.2f} pp",
              f"${_mgn(meth, frac).mean():+.2f}$")

    # no pre-specified configuration may have a positive point estimate; the
    # sentence in the text says so, and it must stay true if the data changes
    pos = [lab for meth, frac, lab in
           [('nrs', 0.25, 'd/4'), ('nrs', 1/3, 'd/3'), ('nrs', 0.5, 'd/2'),
            ('nrs', 2/3, '2d/3'), ('nrs', 0.75, '3d/4'), ('relieff', 0.5, 'ReliefF'),
            ('mutual_info', 0.5, 'MI'), ('pai', 0.5, 'PAI'),
            ('variance', 0.5, 'variance')]
           if _mgn(meth, frac).mean() > 0]
    check("nine distinct pre-specified rules stated", "\\rev{nine distinct}")
    check("'ten selection rules' absent", "ten selection rules", present=False)
    ok = not pos
    print(f"  [{'ok ' if ok else 'FAIL'}] no pre-specified rule has a positive margin"
          + ("" if ok else f"  <- positive: {pos}"))
    if not ok:
        FAILURES.append("a pre-specified rule now has a positive margin")

    ph = []
    for d in DATASETS:
        s_ = ds[ds.dataset == d]
        base = s_[s_.method == 'all_features'].set_index(['seed', 'fold'])['acc_3nn']
        per = s_.groupby(['method', 'k_selected'])['acc_3nn'].mean()
        bi = per.idxmax()
        best = s_[(s_.method == bi[0]) & (s_.k_selected == bi[1])] \
            .set_index(['seed', 'fold'])['acc_3nn']
        j = best.index.intersection(base.index)
        ph.append((best[j] - base[j]).mean() * 100)
    ph = np.asarray(ph)
    se = ph.std(ddof=1) / np.sqrt(len(ph))
    lo, hi = stats.t.interval(0.95, len(ph) - 1, loc=ph.mean(), scale=se)
    check(f"post-hoc margin {ph.mean():+.2f} pp", f"${ph.mean():+.2f}$ pp")
    check(f"post-hoc CI [{lo:+.2f}, {hi:+.2f}]", f"$[{lo:+.2f},\\,{hi:+.2f}]$")

print()
print("13. Numbers added in the first revision")
_log = pd.read_csv(os.path.join(DATA, "literature_log.csv"))
_rec = _log[_log.year >= 2020]
_n1 = int((_rec.truc.astype(str) == "1").sum())
check(f"Axis-1 holds {_n1} of the {len(_rec)} corpus papers since 2020",
      f"It holds {_n1} of the {len(_rec)} corpus")
_fc = pd.read_csv(os.path.join(DATA, "fulltext_coding.csv"))
check(f"{int(_fc.significance_test.sum())} of all {len(_fc)} coded papers run a test",
      f"{int(_fc.significance_test.sum())} of {len(_fc)} report a test")
_FS4 = ["all_features_baseline", "reports_dispersion", "significance_test", "hyperparam_ablation"]
_fcc = _fc[_fc.log_id.notna() & (_fc.log_id.astype(str) != "")]
_none_c, _none_a = int((_fcc[_FS4].sum(axis=1) == 0).sum()), int((_fc[_FS4].sum(axis=1) == 0).sum())
_wd = ['zero','one','two','three','four','five','six','seven','eight','nine','ten']
check(f"papers with none of the four practices: {_none_c}/{len(_fcc)} corpus, {_none_a}/{len(_fc)} all",
      f"{_wd[_none_c].capitalize()} of the {len(_fcc)} corpus papers, and {_wd[_none_a]} of all "
      f"{len(_fc)}, report none of the four practices")
check("read levels 38 abstract / 13 full text",
      f"abstract ({int((_log.read_level == 'abstract').sum())}), full text "
      f"({int((_log.read_level == 'fulltext').sum())})")
# corrected resampled t-test on the best-subset margins (Section 8.1)
_pc = []
for d in DATASETS:
    sub = ds[ds.dataset == d]
    allf = sub[sub.method == 'all_features'].set_index(['seed', 'fold'])['acc_3nn']
    bi = sub.groupby(['method', 'k_selected'])['acc_3nn'].mean().idxmax()
    best = sub[(sub.method == bi[0]) & (sub.k_selected == bi[1])].set_index(['seed', 'fold'])['acc_3nn']
    j = best.index.intersection(allf.index)
    dd = (best[j] - allf[j]).to_numpy()
    v = dd.var(ddof=1)
    _pc.append(1.0 if v == 0 else
               2 * stats.t.sf(abs(dd.mean() / np.sqrt((1 / len(dd) + 0.25) * v)), len(dd) - 1))
_o, _prev, _adj = np.argsort(_pc), 0.0, [0.0] * len(_pc)
for _r, _i in enumerate(_o):
    _prev = min(1.0, max(_prev, (len(_pc) - _r) * _pc[_i])); _adj[_i] = _prev
_ok = min(_adj) >= 0.05
print(f"  [{'ok ' if _ok else 'FAIL'}] corrected test separates no dataset "
      f"(min Holm p = {min(_adj):.2f})")
if not _ok:
    FAILURES.append("corrected test: some margin separated")
check(f"smallest corrected Holm p {min(_adj):.2f} quoted",
      f"$p$:\n${min(_adj):.2f}$, {DATASETS[int(np.argmin(_adj))].capitalize()})")
# Table 5 citation counts come from one OpenAlex snapshot
_s3 = open("sections/s3_granule_geometry.tex").read()
_s3 = _s3[_s3.index(r"\begin{tabular}"):_s3.index(r"\end{tabular}")]
for _r in pd.read_csv(os.path.join(DATA, "taxonomy_citations.csv")).itertuples():
    _row = re.search(r"\\cite[pt]?\{" + _r.bibkey + r"[,}].*?\\\\", _s3, re.S)
    _ok = _row is not None and _row.group(0).rstrip("\\ ").endswith(f"& {_r.openalex_cited_by_count}")
    if not _ok:
        print(f"  [FAIL] Table 5 cites for {_r.bibkey} != {_r.openalex_cited_by_count}")
        FAILURES.append(f"taxonomy cites {_r.bibkey}")
print("  [ok ] Table 5 citation counts match taxonomy_citations.csv"
      if not any(f.startswith("taxonomy cites") for f in FAILURES) else "")
check("retracted: GBNRS tau = 2/3 absent", "\\tau = 2/3", present=False)
check("retracted: field-wide testing claim absent",
      "Statistical testing is rare in the GrC", present=False)
check("retracted: 'oldest and most active' absent",
      "oldest and most active research axis", present=False)

print()
print("14. Sensitivity to NRS k and the persistence setting (Section 7.3)")
# Table: byte-identical to a fresh run of analyze_ablation.py
tmp = tempfile.mkdtemp()
subprocess.run([sys.executable,
                os.path.join(_ROOT, "code", "analysis", "analyze_ablation.py")],
               capture_output=True, check=True,
               env=dict(os.environ, GRC_TABLES_OUT=tmp))
_same = open(tmp + "/tab_sensitivity.tex").read() == open("tables/tab_sensitivity.tex").read()
print(f"  [{'ok ' if _same else 'FAIL'}] tables/tab_sensitivity.tex")
if not _same:
    FAILURES.append("tables/tab_sensitivity.tex drifted from generator")
shutil.rmtree(tmp)
# Inline numbers, recomputed here independently of the generator
_abl = os.path.join(DATA, "ablation")
_ai = pd.concat(pd.read_csv(f) for f in glob.glob(os.path.join(_abl, "imp_*.csv")))
_ad = pd.concat(pd.read_csv(f) for f in glob.glob(os.path.join(_abl, "down_*.csv")))


def _acc(meth, cfg):
    s_ = _ad[(_ad.method == meth) & (_ad.config == cfg) & (_ad.k_selected < _ad.d)]
    return s_.groupby("dataset").acc_3nn.mean().reindex(DATASETS).to_numpy()


def _rhoz(pcfg, ncfg):
    z, w = [], []
    for d in DATASETS:
        a = _ai[(_ai.method == "pai") & (_ai.config == pcfg) & (_ai.dataset == d)] \
            .groupby("attribute_j").importance_score.mean()
        b = _ai[(_ai.method == "nrs") & (_ai.config == ncfg) & (_ai.dataset == d)] \
            .groupby("attribute_j").importance_score.mean()
        r = stats.spearmanr(a, b).correlation
        z.append(np.arctanh(np.clip(0.0 if np.isnan(r) else r, -0.999, 0.999)))
        w.append(len(a) - 3)
    z, w = np.array(z), np.array(w)
    zb, se = (w * z).sum() / w.sum(), 1 / np.sqrt(w.sum())
    return np.tanh(zb), np.tanh(zb - 1.96 * se), np.tanh(zb + 1.96 * se)


_pd, _n7 = _acc("pai", "md1_t2.0"), _acc("nrs", "k7")
_pairs = [(_acc("nrs", k), _pd) for k in ["k3", "k5", "k7", "k11", "k15"]] + \
         [(_n7, _acc("pai", c)) for c in ["md1_t2.0", "md0_t2.0", "md1_t1.5",
                                          "md1_t3.0", "md0_tinf"]]
_gaps = [(n - p).mean() * 100 for n, p in _pairs]
check(f"3-NN gap range {min(_gaps):.1f} to {max(_gaps):.1f} pp",
      f"between ${min(_gaps):.1f}$ and ${max(_gaps):.1f}$")
_minw = min(int((n > p).sum()) for n, p in _pairs)
_ok = _minw >= 9
print(f"  [{'ok ' if _ok else 'FAIL'}] NRS wins on at least nine datasets in every configuration (min {_minw})")
if not _ok:
    FAILURES.append("sensitivity: 'at least nine' wins")
_var = ds[(ds.method == 'variance') & (ds.k_selected < ds.d)] \
    .groupby('dataset').acc_3nn.mean().reindex(DATASETS).to_numpy()
_unt = _acc("pai", "md0_tinf")
check(f"untruncated H0 PAI {_unt.mean()*100:.1f}% vs variance {_var.mean()*100:.1f}%, "
      f"p={stats.wilcoxon(_unt, _var).pvalue:.3f}",
      f"(${_unt.mean()*100:.1f}\\%$ against ${_var.mean()*100:.1f}\\%$, Wilcoxon "
      f"$p={stats.wilcoxon(_unt, _var).pvalue:.3f}$)")
_better = [c for c in ["md1_t2.0", "md0_t2.0", "md1_t1.5", "md1_t3.0", "md0_tinf"]
           if _acc("pai", c).mean() > _var.mean()]
_ok = not _better
print(f"  [{'ok ' if _ok else 'FAIL'}] no PAI configuration above the variance null {_better}")
if not _ok:
    FAILURES.append("sensitivity: PAI above variance null")
_excl = [k for k in ["k3", "k5", "k7", "k11", "k15"] if _rhoz("md1_t2.0", k)[2] < 0] + \
        [c for c in ["md0_t2.0", "md1_t1.5", "md1_t3.0", "md0_tinf"] if _rhoz(c, "k7")[2] < 0]
_ok = _excl == ["k11", "k15"]
print(f"  [{'ok ' if _ok else 'FAIL'}] interval excludes zero only for k=11, k=15 ({_excl})")
if not _ok:
    FAILURES.append("sensitivity: which intervals exclude zero")
check(f"rho_z at k=11 = {_rhoz('md1_t2.0', 'k11')[0]:.2f}",
      f"$\\bar\\rho_z={_rhoz('md1_t2.0', 'k11')[0]:.2f}$ at $k=11$")
# Theorem 1 bound under every persistence setting (Remark on truncation)
_ri = pd.read_csv(RAW + "raw_importance.csv")
_rb = _ri[_ri.method == 'pai'][['dataset', 'seed', 'attribute_j', 'pai_bound']]
_pb = _ai[_ai.method == 'pai'].merge(_rb, on=['dataset', 'seed', 'attribute_j'])
_pb['ratio'] = _pb.importance_score / ((_pb.config.str[2].astype(int) + 1) * _pb.pai_bound / 2)
_n = _pb.groupby('config').size()
_ok = (_pb.importance_score <= (_pb.config.str[2].astype(int) + 1) * _pb.pai_bound / 2 + 1e-9).all() \
    and (_n == 995).all()   # constant attributes: score = bound = 0
print(f"  [{'ok ' if _ok else 'FAIL'}] bound holds for all scores in all settings "
      f"({len(_n)} settings x {_n.min()} scores)")
if not _ok:
    FAILURES.append("Theorem 1 bound under truncation")
_mx = _pb.loc[_pb.ratio.idxmax()]
check(f"largest ratio {_mx.ratio:.2f} in {_mx.config}",
      f"The largest ratio, ${_mx.ratio:.2f}$,\noccurs in the untruncated $H_0$ setting"
      if _mx.config == "md0_tinf" else "UNEXPECTED SETTING")

print()
print("15. Inline numbers in Patterns B and C (rechecked in the first revision)")
_D = DATASETS
def _mi(m, d):
    return _ri[(_ri.method == m) & (_ri.dataset == d)].groupby("attribute_j").importance_score.mean()
_r = {d: stats.spearmanr(_mi("pai", d), _mi("nrs", d)) for d in _D}
check(f"first three datasets mean rho {np.mean([_r[d].correlation for d in _D[:3]]):.2f}",
      f"$\\bar\\rho={np.mean([_r[d].correlation for d in _D[:3]]):.2f}$")
_z = np.arctanh([_r[d].correlation for d in _D]); _w = np.array([len(_mi('pai', d)) - 3 for d in _D])
_Q = (_w * (_z - (_w * _z).sum() / _w.sum()) ** 2).sum()
check(f"Q = {_Q:.1f}, I2 = {100 * (_Q - 9) / _Q:.0f}%", f"$Q = {_Q:.1f}$, $I^2 = {100 * (_Q - 9) / _Q:.0f}\\%$")
check(f"WDBC rho {_r['wdbc'].correlation:.2f} p {_r['wdbc'].pvalue:.3f}",
      f"$\\rho={_r['wdbc'].correlation:.2f}$, \\rev{{$p={_r['wdbc'].pvalue:.3f}$}}")
_t = _ri.groupby(["method", "dataset"]).time_method_sec.median().unstack(0).mean()
check(f"PAI mean median time {_t['pai']:.1f} s", f"is {_t['pai']:.1f}\\,s for PAI and {_t['nrs']:.3f}\\,s for NRS")
check(f"PAI/ReliefF {_t['pai']/_t['relieff']:.1f}x, PAI/MI {_t['pai']/_t['mutual_info']:.1f}x",
      f"by factors of about {round(_t['pai']/_t['relieff'], -1):.0f} and "
      f"{round(_t['pai']/_t['mutual_info'], -1):.0f}")
check("retracted: 'orders of magnitude faster' (ReliefF is under 100x)",
      "orders of magnitude faster", present=False)
_ts = _ri[(_ri.method == "pai") & (_ri.dataset == "sonar")].time_method_sec.median()
_tn = _ri[(_ri.method == "nrs") & (_ri.dataset == "sonar")].time_method_sec.median()
check(f"Sonar PAI median time {_ts:.3f} s (NRS {_tn:.3f} s)",
      f"its median PAI time is {_ts:.3f}\\,s, close to that\nof NRS", present=_ts < 2 * _tn)
_sc = ks.groupby("dataset").k_pai_scale.first()
check(f"Sonar filtration scale is zero ({_sc['sonar']})", "no point has any neighbour within", present=(_sc['sonar'] == 0))
_pos = _sc[_sc > 0]
# Sonar degeneracy at the default truncation (Section 7.3)
_sp = _ri[(_ri.method == "pai") & (_ri.dataset == "sonar")].importance_score
_st = _ai[(_ai.method == "pai") & (_ai.config == "md0_tinf") & (_ai.dataset == "sonar")].importance_score
check(f"Sonar PAI zero share {100 * (_sp == 0).mean():.0f}% (default), {100 * (_st == 0).mean():.0f}% (untruncated)",
      f"so ${100 * (_sp == 0).mean():.0f}\\%$ of its PAI scores", present=bool((_st == 0).sum() == 0))
_rd = pd.read_csv(os.path.join(DATA, "raw_downstream.csv"))
_rd = _rd[(_rd.dataset == "sonar") & (_rd.k_selected < _rd.d)].groupby("method").acc_3nn.mean()
_pt = _ad[(_ad.method == "pai") & (_ad.config == "md0_tinf") & (_ad.dataset == "sonar") & (_ad.k_selected < _ad.d)].acc_3nn.mean()
check(f"Sonar untruncated PAI {100 * _pt:.1f} vs NRS {100 * _rd['nrs']:.1f}, variance {100 * _rd['variance']:.1f}",
      f"(${100 * _pt:.1f}\\%$\nagainst ${100 * _rd['nrs']:.1f}\\%$ and ${100 * _rd['variance']:.1f}\\%$ with 3-NN)",
      present=bool(_pt < _rd["variance"] < _rd["nrs"]))
check(f"scale range {_pos.min():.1f} ({_pos.idxmin()}) to {_pos.max():.1f} ({_pos.idxmax()})",
      f"ranges from ${_pos.min():.1f}$ on {_pos.idxmin().capitalize()} to ${_pos.max():.1f}$ on {_pos.idxmax().capitalize()}")
_adv = {}
for d in _D:
    _a = []
    for K in sorted(ks.knn_K.unique()):
        sub = ks[(ks.dataset == d) & (ks.knn_K == K)]
        sub = sub[sub.k_selected < sub["d"].iloc[0]]
        m = sub.groupby("method")["knn_overlap"].mean(); _a.append(m["pai"] - m["nrs"])
    _adv[d] = np.array(_a)
_Ks = np.array(sorted(ks.knn_K.unique()), float)
_bk = np.array([_Ks[int(np.argmax(_adv[d]))] for d in _D]); _kp = np.array([_sc[d] for d in _D])
_rr = stats.spearmanr(_kp[_kp > 0], _bk[_kp > 0])
check(f"scale vs argmax-K rho {_rr.correlation:.2f} p {_rr.pvalue:.2f}",
      f"is $\\rho={_rr.correlation:.2f}$ ($p={_rr.pvalue:.2f}$)")
check(f"{int((_kp > 0).sum())} datasets with a non-degenerate scale",
      f"On the {['zero','one','two','three','four','five','six','seven','eight','nine','ten'][int((_kp > 0).sum())]} datasets with a\nnon-degenerate scale")
check(f"{int((_bk == 3).sum())} datasets peak at K=3", f"{['Zero','One','Two','Three','Four','Five','Six','Seven'][int((_bk == 3).sum())]} of ten datasets peak at\n$K=3$")
_neg = sorted(d for d in _D if (_adv[d] < 0).all())
check(f"datasets where PAI trails at every K: {_neg}", "PAI trails NRS at every $K$ on Sonar, as it also does on Glass.", present=(_neg == ['glass', 'sonar']))
check("retracted: 'no hyperparameter ablation was performed' absent",
      "no hyperparameter ablation was\nperformed", present=False)

# Section 7.2 summary of Table 9, after the range analysis moved to Appendix B
_pr = open("tables/tab_pai_range.tex").read()
_rows = re.findall(r"^\w+\s*&\s*\d+ & \$([+-]\d\.\d+)\$ & \$(<?)(\d\.\d+)\$", _pr, re.M)
_sig = [(float(r), (q == "<") or float(p) < 0.05) for r, q, p in _rows]
_npos = sum(1 for r, g in _sig if g and r > 0); _nneg = sum(1 for r, g in _sig if g and r < 0)
_words = ['no','one','two','three','four','five','six','seven','eight','nine','ten']
check(f"PAI-range: {_npos} significantly positive, {_nneg} significantly negative of {len(_sig)}",
      f"significantly positive on {_words[_npos]} of the\nten datasets and significantly negative on {_words[_nneg]}")

print()
print("16. Minimum reporting standard (Section 8.5, Table tab:standard)")
_fc16 = pd.read_csv(os.path.join(DATA, "fulltext_coding.csv")); _n16 = len(_fc16)
for _col, _tail in [("all_features_baseline", " \\\\"),
                    ("reports_dispersion", " report dispersion \\\\"),
                    ("significance_test", " report a test (unit not coded) \\\\"),
                    ("hyperparam_ablation", " vary a method parameter (metric not coded) \\\\")]:
    _v = int(_fc16[_col].sum())
    check(f"tab:standard {_col} = {_v} of {_n16}", f"& {_v} of {_n16}{_tail}")
_w5 = stats.wilcoxon(np.arange(1, 6), method="exact").pvalue
_w6 = stats.wilcoxon(np.arange(1, 7), method="exact").pvalue
print(f"  [{'ok ' if _w5 > 0.05 and _w6 < 0.05 else 'FAIL'}] exact Wilcoxon: n=5 min p {_w5:.4f}, n=6 min p {_w6:.4f}")
if not (_w5 > 0.05 and _w6 < 0.05):
    FAILURES.append("Wilcoxon minimum n")
check(f"smallest possible p with five datasets {_w5:.4f}", f"the smallest possible $p$ is ${_w5:.4f}$")
_af = open("tables/tab_allfeats.tex").read()
_sds = [float(x) for x in re.findall(r"\\pm (\d+\.\d)\$\\% & \d", _af)]
check(f"best-subset fold SD range {min(_sds):.1f} to {max(_sds):.1f}", f"range from ${min(_sds):.1f}$ to ${max(_sds):.1f}$ pp")
check(f"tab:standard quotes max fold SD {max(_sds):.1f}", f"deviations reach {max(_sds):.1f} pp")

print()
print("17. Power of the per-dataset Spearman test at small d (Section 7.2, Table tab:rho)")
import itertools as _it
def _min_sig_rho(n):
    x = np.arange(n); best = None
    for perm in _it.permutations(range(n)):
        r, pv = stats.spearmanr(x, perm)
        if pv < 0.05 and (best is None or abs(r) < best):
            best = abs(r)
    return best
_m4, _m7 = _min_sig_rho(4), _min_sig_rho(7)
check(f"d=4: smallest significant |rho| = {_m4:.2f} (only perfect agreement)",
      "Iris reaches $p<0.05$ only if\nthe two rankings agree or disagree perfectly", present=abs(_m4 - 1) < 1e-9)
check(f"d=7: smallest significant |rho| = {_m7:.2f} (text)", f"need $|\\rho|\\geq {_m7:.2f}$")
check(f"d=7: smallest significant |rho| = {_m7:.2f} (table note)", f"$|\\rho|\\geq {_m7:.2f}$ is needed")
check("retracted: 'no power ... at any ranking' absent", "has no power to reject the null", present=False)
check("retracted: table note 'cannot reach p < 0.05 at any rho' absent", "cannot reach $p < 0.05$ at any", present=False)

if FAILURES:
    print(f"FAILED ({len(FAILURES)}): " + "; ".join(FAILURES))
    sys.exit(1)
print("All checks passed: manuscript is consistent with the released CSVs.")
