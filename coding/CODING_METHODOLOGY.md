# Failure-pattern coding of the 51-paper corpus

**Status: full-text coding for 11 of the 13 imports (2 unobtainable). Needs co-author (full-text) validation before submission.**
**Editorial clarification (2026-09-10):** The AIR table reports the existing
ten preliminary A-related codes, including partial cases, not ten failed
methods. Intended equivalence, reuse with novelty elsewhere, and unsupported
novelty must be distinguished during source-level validation. No validated
3/4/3 subdivision is available in the CSV; that subdivision has been removed
from the manuscript. The historical wording below is a working rationale,
not a validated prevalence estimate. No original paper has been newly
validated by this editorial revision.

Produced to address review R2 finding MAJOR-1 ("the thesis is not evidenced
against the survey's own corpus"). Companion file: `failure_pattern_coding.csv`.

---

## 1. What was coded

Each of the 51 papers in `literature_log.csv` received two judgements.

### 1a. Import status  — `import_status`

| Value | Meaning |
|---|---|
| `import` | The paper brings an **external** mathematical or ML framework — persistent homology / TDA, abstract or fuzzy topology, weak / partial-label / label-distribution supervision, or a neural component — **into the GrC core pipeline** (neighbourhood granule → approximation → reduct). |
| `internal` | The paper develops granular computing **from within**: granular-ball geometry, discernibility-matrix acceleration, three-way decision, a neighbourhood measure built out of known approximation operators, an application of an existing GrC method. Granular balls, fuzzy-rough sets and three-way decision are treated as **native** to rough-set theory, not imports. |
| `background` | Foundational theory or a prior survey cited for context (Bayes-error bounds, FS surveys, fuzzy-rough classics, a weak-supervision survey). No GrC method of its own. |

This judgement is **high-confidence for almost every paper** — it can be made
from title + abstract + the `key_claim` / `key_finding` fields already in the
log.

### 1b. Failure pattern  — `pattern` (importing papers only)

Definitions taken verbatim from §7:

- **A — Reduction to a known granular quantity.** Once the new quantity is
  unfolded it coincides with, or is trivially bounded by, a quantity already in
  the GrC literature. Diagnostic: is it a monotone transformation of an
  existing granular measure (bounded, non-vanishing Jacobian)?
- **B — Dominance of label-orthogonal geometry.** The importance signal is
  driven by geometry of the feature distribution that is orthogonal to the
  decision (measurement scale is the special case a stability bound captures).
- **C — Self-optimising evaluation.** The method wins only where the evaluation
  metric is algebraically tied to its objective, or only in part of the range
  of a free metric parameter the analyst sets.

| Value | Meaning |
|---|---|
| `A`, `C`, `A + C` | Evidence supports this pattern. Assigned at **full confidence only where the manuscript body already carries the argument** (§4.1 abstract topology, §4.3 TDA). |
| `A (partial)` | The paper is taxonomic — it shows an equivalence to known operators but makes no independent performance claim to "reduce". |
| `unclassified` | The paper imports a framework, but screening-level evidence is **insufficient** to assign A/B/C. Left explicit rather than forced. |
| `n/a` | `internal` or `background` paper — the diagnostic does not apply. |

### Confidence / evidence tiers

- `confidence` ∈ {high, med, low}
- `evidence` ∈ {`body` = argued in the manuscript §3/§4/§7 · `log` = from the
  `key_claim`/`key_finding` fields · `log+body` · `title`}

---

## 2. Distribution

| Category | Papers |
|---|---:|
| **Imports an external framework** | **13** |
| &nbsp;&nbsp;→ coded Pattern A (incl. 4 partial, 1 also Pattern C) | **10** |
| &nbsp;&nbsp;→ coded Pattern B only | **0** |
| &nbsp;&nbsp;→ insufficient evidence to code (needs full text) | 3 |
| **Internal GrC development** (A/B/C not applicable) | **23** |
| **Background / foundational reference** | **15** |
| **Total** | **51** |

### By axis

| Axis | background | import | internal |
|---|---:|---:|---:|
| 1 — Granule geometry | 3 | 3 | 18 |
| 2a — Abstract topology | 0 | 6 | 0 |
| 2b — Computational topology (TDA) | 2 | 1 | 0 |
| 3 — Efficiency / discernibility | 2 | 0 | 4 |
| 4 — Sufficiency / limits | 8 | 3 | 0 |
| 5 — (stray tag) | 0 | 0 | 1 |

### The 13 importing papers

| id | ref | framework | pattern | conf. |
|---|---|---|---|---|
| T2A_05 | Zhang 2009 | Alexandrov topology | **A** | high |
| T4_09 | Dai T.T. 2024 | intuitionistic fuzzy topology | **A + C** | high |
| T2B_01 | Kindelan 2021 (TDABC) | TDA / persistent homology | **A** | high |
| T2A_02 | Yao W. 2023 | Alexandrov topology | A | med |
| T2A_03 | Al-shami 2025 | general topology (δ-open sets) | A | med |
| T2A_01 | Zhu 2007 | point-set topology | A (partial) | med |
| T4_11 | Qian W. 2022 | weak sup. (incomplete-label LDL) | **A** | med |
| T4_12 | Qian W. 2023 | weak sup. (partial-label) | **A (partial)** | high |
| T1_14 | Qian W. 2023 | weak sup. (label distribution) | **A (partial)** | med |
| T4_10 | Qian W. 2024 | weak sup. (partial-label) | **A (partial)** | med |
| T2A_01 | Zhu 2007 | point-set topology | A (partial) | med |
| T2A_04 | Wang Xue 2019 | topology (CRT spaces) | unclassified | low |
| T1_03 | Zhang 2025 | neural (learned attribute weights) | unclassified | low |
| T1_04 | Sun 2025 | label enhancement (multi-label) | unclassified | low |

---

## 3. What this coding supports — and what it does not

**Supports.** Among the 13 corpus papers that import an external framework,
**Pattern A is the dominant observed failure mode: 10 of 13**, spanning three
sub-literatures — abstract topology (5 of 6 Axis-2a papers), the TDA classifier
(T2B_01), and all four granular-ball / rough-set methods for weak & partial-label
supervision (T1_14, T4_10, T4_11, T4_12), whose feature-importance score is the
(fuzzy) rough dependency degree recomputed on disambiguated labels. The A/B/C
diagnostic is aimed at this ~13-paper cross-disciplinary stream, not at the ~23
internal-development papers that make up the bulk of the corpus.

The four weak-supervision papers were read at full text (2026-09-09):
- **T4_12 (PFFL, Information Fusion 2023)** — Definition 1 writes the NRS
  dependency degree γ = |POS|/|U| verbatim; feature significance fuses that γ
  with a label-consistency term, on granular-ball-disambiguated labels. High
  confidence.
- **T4_11 (local RS, IJMLC 2022)** — "local rough set" = NRS on the labelled
  sub-universe; significance = increment of the neighbourhood inclusion
  (dependency) degree. Clean Pattern A.
- **T1_14 (GBFRS, KBS 2023)** and **T4_10 (LDFS, ASOC 2024)** — feature
  significance = granular-ball / weighted **fuzzy dependency** on a
  label-similarity relation, plus a secondary term (local consistency /
  feature discernibility). Pattern A (partial).
- All four report a no-selection baseline, a Friedman/Bonferroni–Dunn test and
  a hyperparameter sweep — Pattern A is about the quantity, not the rigour.

**Does not support.**
1. Any claim that imported quantities *in general* "tend to" exhibit B or C.
   **Pattern B has zero corpus instances**; both B and C are established
   through the manuscript's own experiments, which use a persistence-based
   score the authors built (`PAI`), not a third-party method.
2. A *re-implementation-level* verification. 10 of 13 importing papers are
   coded from a single full-text read, not a re-run; the Pattern-A calls should
   still be re-checked (esp. whether T2A_02/T2A_03 make a "reduces" performance
   claim or are purely taxonomic like T2A_01).
3. Anything about the 3 remaining `unclassified` papers (T1_03 neural weighting,
   T1_04 multi-label label enhancement, T2A_04 covering-topology). Lower
   priority — none is central to the four survey axes.

---

## 4. Co-author action before submission

1. **Re-check the 5 topology Pattern-A calls** (T2A_01–03, T2A_05, confirm
   T2B_01) against the full text — especially whether T2A_02/T2A_03 make a
   "reduces" performance claim or are purely taxonomic like T2A_01.
2. Optionally code the 3 remaining `unclassified` papers (low priority).
3. **Decide the thesis wording.** The manuscript now carries §7.4 + Table 10 +
   the Appendix A note, and §1 has a one-sentence pointer that Pattern A is the
   dominant *observed* mode while B/C rest on the experiments. If you want to
   keep the stronger "tend to (A) … (B) … (C)" phrasing in the §1 quote block
   and the abstract, it must be reconciled with Table 10 — this is a PI call,
   and it is coupled to review Action 2 (abstract scope: realised vs
   prospective imports).
4. **Merge the validated `failure_pattern` column back into
   `literature_log.csv`** and re-release, replacing the current all-`none`
   column.

---

*Coder: import-status from the systematic-review log + titles/abstracts;
failure-pattern from the manuscript body (topology, TDA) and from a full-text
read of the four weak-supervision papers (T1_14, T4_10, T4_11, T4_12) on
2026-09-09. No method was re-implemented.*
