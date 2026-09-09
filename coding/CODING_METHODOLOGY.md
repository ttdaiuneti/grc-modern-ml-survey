# Import coding of the 51-paper corpus

Companion file: `failure_pattern_coding.csv`. Produced to answer review finding
"the thesis is not evidenced against the survey's own corpus". Every one of the
51 papers in `literature_log.csv` carries an import-status judgement; every one
of the 13 cross-framework imports carries a claim-class judgement made from the
full text.

---

## 1. Import status — `import_status`

| Value | Meaning | Count |
|---|---|---:|
| `import` | Brings an **external** framework — persistent homology / TDA, abstract or fuzzy topology, weak / partial-label / label-distribution supervision, or a neural component — **into the GrC core pipeline** (neighbourhood granule → approximation → reduct). | **13** |
| `internal` | Develops granular computing **from within**: granular-ball geometry, discernibility acceleration, three-way decision, a neighbourhood measure built from known approximation operators, or an application of an existing GrC method. Granular balls, fuzzy-rough sets and three-way decision are treated as native to rough-set theory, not imports. | **23** |
| `background` | Foundational theory or a prior survey cited for context (Bayes-error bounds, feature-selection surveys, fuzzy-rough classics). No GrC method of its own. | **15** |

This judgement can be made from title + abstract + the `key_claim` /
`key_finding` fields already in the log, and is high-confidence for almost
every paper.

### By axis

| Axis | background | import | internal |
|---|---:|---:|---:|
| 1 — Granule geometry | 3 | 3 | 18 |
| 2a — Abstract topology | 0 | 6 | 0 |
| 2b — Computational topology (TDA) | 2 | 1 | 0 |
| 3 — Efficiency / discernibility | 2 | 0 | 4 |
| 4 — Sufficiency / limits | 8 | 3 | 0 |
| 5 — evaluation-methodology (not a survey axis; one paper, T5_01) | 0 | 0 | 1 |

---

## 2. Claim class — `claim_class` (the 13 imports only)

All 13 imports reuse a quantity already established in the field (a dependency
degree, a positive region, a discernibility set). Reuse by itself is not a
finding; the class records **what the paper claims for the quantity it
reuses**.

| Class | Test applied | Count |
|---|---|---:|
| **(a)** the equivalence / characterisation **is** the contribution | the full text contains no classification experiment | **5** |
| **(b)** the quantity is reused as a component; the stated novelty is a different construction, and a baseline comparison plus a significance test are reported | | **7** |
| **(c)** an accuracy or reduct-size improvement is attributed to the reused quantity itself, on support that does not carry the attribution | | **1** |

The legacy `pattern` column (`A`, `A (partial)`, `A (equivalence)`, `A + C`) is
kept for continuity with earlier drafts; `claim_class` is the column the
manuscript's Table 10 and §7.5 use.

### The 13 importing papers

| id | ref | framework | class | provenance basis |
|---|---|---|:--:|---|
| T2A_01 | Zhu 2007 | point-set topology | a | Inf Sci 177:1499–1508; axiomatic-systems section, conditions for two coverings to give the same approximation operator. No experiments. |
| T2A_02 | Yao & Han 2023 | Alexandrov topology | a | Inf Sci 627:238–250; four RS models shown to be instances of one Alexandrov framework. No experiments. |
| T2A_03 | Al-Shami & Al Nuwairan 2025 | general topology (δ-open sets) | a | J Math 2025 art. 8990430; Table 1 is a worked example; paper states the accuracy measure "decreases for some subsets" vs the existing one. No experiments. |
| T2A_04 | Wang & Ma 2019 | topology (CRT spaces) | a | CAAI Trans Intel Tech, doi 10.1049/trit.2019.0008; Theorems 1–6 give equivalent conditions for separation axioms; Conclusion claims equivalence results only. No experiments. |
| T2A_05 | Zhang et al. 2009 | Alexandrov topology | a | Inf Sci 179:471–473; three-page note showing a proposed generalised RS was already the known Alexandrov structure. No experiments. |
| T1_14 | Sun/Qian 2023 | weak sup. (label distribution) | b | Knowl-Based Syst 2023; granular-ball fuzzy dependency on a label-similarity relation, plus a local-consistency term; no-selection baseline, Friedman + Bonferroni–Dunn. |
| T4_10 | Qian et al. 2024 | weak sup. (partial-label) | b | Appl Soft Comput 161:111692; weighted fuzzy-rough dependency + label significance fused with feature discernibility; 'Base' baseline (Fig 7), Bonferroni–Dunn. |
| T4_11 | Qian et al. 2022 | weak sup. (incomplete-label LDL) | b | Int J Mach Learn Cybern 13:2345–2364; 'local rough set' = NRS on the labelled sub-universe; significance = increment of the neighbourhood inclusion degree; Friedman + Bonferroni–Dunn. |
| T4_12 | Qian et al. 2023 | weak sup. (partial-label) | b | Inf Fusion 94:152–169; Definition 1 writes γ = \|POS\|/\|U\| verbatim; significance = NRS significance on disambiguated labels + a label-consistency term; ablation shows dependency alone does not beat the baseline. |
| T1_03 | Zhang et al. 2025 | neural (learned attribute weights) | b | Neural Networks 185:107178; Defs 4–5 state the granular-ball positive region and dependency function; Algorithm 1 step S3 uses those dependencies as the ANN's initial weights and refines them; original-dataset baseline, Friedman + Nemenyi. |
| T1_04 | Sun et al. 2025 | label enhancement (multi-label) | b | Eng Appl Artif Intell 145:110191; dependency degree cited to Sun et al. 2021a and combined with mutual information; contribution is the label-enhancement step; all-features condition + Friedman + Nemenyi (Table 8). |
| T2B_01 | Kindelan et al. 2024 | TDA / persistent homology | b | Adv Data Anal Classif 18:493–538; Def. 2 star/link, Defs. 5–7 association/extension/labeling functions carry the novelty; compared against KNN, weighted-KNN, linear SVM, RF on eight datasets; result described as "competitive". No significance test. |
| T4_09 | Tran et al. 2024 | intuitionistic fuzzy topology | c | Soft Computing 28:11799–11822; the IFT-subbasis significance measure is a monotone function of the pre-order α-cut chain; 50 %/10 % gains reported across 25 tables with no significance test. **Authors' own prior work.** |

`provenance` and `evidence = fulltext` are populated for all 13 rows in the
CSV. Two rows (T1_14, T4_10) keep `confidence = med`: the fuzzy-dependency
reuse there is through a secondary term and the class-(b) call rests on a
judgement about where the novelty sits, not on an explicit statement in the
paper.

---

## 3. What this coding supports — and what it does not

**Supports.** All 13 corpus papers that import an external framework reuse a
granular quantity already in the field. Read at full text: 5 are equivalence
or characterisation results in which the equivalence is the contribution and
no performance comparison is reported; 7 reuse the quantity as a component,
report a baseline and a significance test, and locate their novelty elsewhere
in the pipeline; 1 attributes a performance improvement to the reused quantity
on support that does not carry it, and that one is the authors' own prior
work. This is the picture Table 10 and §7.5 report. The diagnostic is aimed at
this 13-paper cross-disciplinary stream, not at the 23 internal-development
papers.

**Does not support.**
1. Any claim that imported quantities *in general* exhibit Pattern B or C.
   **Pattern B has zero corpus instances.** B and C are established through the
   manuscript's own experiments, which use a persistence-based score the
   authors constructed (PAI), not a third-party method.
2. A re-implementation-level verification. The coding rests on one full-text
   read of each paper, not a re-run. The `provenance` column names the
   definition, theorem or stated limitation each class rests on so that an
   individual call can be checked against the source.
3. Inter-coder reliability. The coding was done by one author. Independent
   replication of the assignments is future work.

## 4. Genre composition of the 13 (stated in §7.5)

The import set is not a random sample of GrC extensions: 6 of the 13 are
abstract-topology papers that run no experiments and therefore cannot exhibit
B or C by construction; 4 are from one group (Qian Wenbin and co-authors); 2
are Axis-1 methods; 1 is the self-citation. The 5 / 7 / 1 split is partly
determined by this composition, and §7.5 says so.

---

*Coder: import-status from the systematic-review log plus titles/abstracts;
claim class from a full-text read of all 13 imports (nine PDFs in
`AIR/coding/fulltext/`, four in `AIR/coding/qian_fulltext/`). No method was
re-implemented.*
