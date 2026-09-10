# Full-text evidence review

Date: 2026-09-10. Target: the updated AIR manuscript and its 13-record
cross-framework coding set. All seven requested PDFs are present; together
with the six existing papers, no PDF is missing from this set.

This is a focused assistant-assisted audit of contribution statements,
selected definitions/algorithms and relevant results, not an exhaustive
verification of every theorem or a reproduction of experiments. Page numbers
below refer to printed article pages unless explicitly described as PDF pages.
Source statements and audit inferences are distinguished. Author adjudication
is still needed, particularly for the IFT case.

## Decisions

The current 5/8 membership is a descriptive grouping. It is not
evidence that all 13 complete methods reduce to a known granular quantity.
The five theory papers do not count as failures merely for giving equivalences.
The eight methodological cases need not report significance tests to belong
to that category. Following author clarification, IFT + wrapper is evaluated
as a combined method and assigned class b, not the former class c.
This supersedes the historical 5/7/1 split and A+C label. It does not validate
the isolated criterion or the evaluation protocol.

| ID | Descriptive class | Source anchor | Audited interpretation |
|---|---|---|---|
| T2A_01 | a | Zhu 2007, pp. 1502-1506, Theorems 1-10; conclusion p. 1507 | Characterises covering approximations and conditions for equal operators. This is a theoretical contribution, not a failed classifier. |
| T2A_02 | a | Yao & Han 2023, pp. 248-249, Theorems 5.3, 5.5, 5.7; Remark 5.8; conclusion | Correspondence concerns preorders, Alexandrov neighbourhoods and covering-induced minimal neighbourhoods. The authors explicitly separate known correspondences from their Section 4 contributions. |
| T2A_03 | a | Al-Shami & Al Nuwairan 2025, pp. 9-11, Section 6, Eq. (10), Table 1 | Gives set-approximation comparisons and acknowledges reduced approximation accuracy for some comparisons. No demonstrated classifier gain; no blanket smaller-boundary conclusion. |
| T2A_04 | a | Wang & Ma 2019, pp. 131-134, Definition 9, Theorems 1-6 | Separation-axiom characterisation for CRT spaces, with explicit hypotheses. No classification experiment is needed to establish this genre. |
| T2A_05 | a | Zhang et al. 2009, pp. 472-473, Theorems 2.1 and 3.1; final remark | The note diagnoses the correspondence in Qin et al. (2008). Zhang is the source of the critique, not its target. |
| T1_03 | b | Zhang et al. 2025, PDF pp. 4-5, Definitions 4-5, Algorithms 1-2, steps S3-S5 | Positive-region/dependency quantities initialise an ANN; subsequent weight updates are a distinct stage. Initialisation reuse is not proof of identical final rankings. |
| T1_04 | b | Sun et al. 2025, PDF p. 8, Definitions 24-26, Eqs. (31)-(33) | The mixed score combines dependency, mutual information and knowledge granularity, then aggregates ball-wise scores. It is not dependency alone. |
| T1_14 | b | Qian et al. 2023, Eq. (4.22), Definition 13; Section 5.7 | GBFRS adds dependency-based and local-consistency significance. Any whole-score equivalence must account for the second term. The first author is Qian, not Sun. |
| T4_10 | b | Qian et al. 2024, PDF p. 7, Definition 11, Eq. (18); Section 5.4 | LDFS mixes label-weighted fuzzy dependency and feature discernibility. Component reuse does not prove whole-score equivalence. |
| T4_11 | b | Qian et al. 2022, p. 2351, Definitions 4-6, Eqs. (7)-(9) | LRFS uses a positive-region fraction with denominator the labelled sub-universe, then a dependency increment. Preserve the local model and its thresholds rather than calling it ordinary NRS without qualification. |
| T4_12 | b | Qian et al. 2023, p. 160, Definition 12, Eq. (18); Section 5.5 | PFFL weights dependency significance and label-consistency significance. Its publication pages are 152-168, not 152-169. |
| T2B_01 | b, comparison case | Kindelan et al. 2024, pp. 505-507, Definitions 5-7, Eqs. (8)-(10); p. 516, Section 4.4 | Simplicial label propagation with inverse squared filtration-value weights. Not a rough-set reduct method and not proved equivalent to an unweighted radius vote or NRS. |
| T4_09 | b, combined method | Dai et al. 2024, pp. 11803-11805, Definitions 5.1-5.3, Eqs. (6)-(9), Algorithms 1-2; pp. 11814, 11818-11819 | FW_IFT combines the subbasis criterion with wrapper search. Results concern that combined procedure. Separate attribution requires alternative criteria under the same wrapper and budget. Needing a wrapper is not A+C. |

## Main corrections and rationale

### 1. Equivalence studies are not failed imports

Yao & Han's conclusion on p. 249 explicitly acknowledges that many results
in Sections 2, 3 and 5 are already available, while locating claimed new
composition/decomposition and Galois-adjunction results in Section 4.
An audit must assess those actual claims, not declare the whole paper
non-novel because preorders correspond to Alexandrov topologies.

Zhang's final remark assesses Qin et al. (2008), DOI
10.1016/j.ins.2008.07.002. If the survey makes its own adverse novelty verdict
about Qin, it should inspect that original paper and cite it as the target.
It must not count Zhang's diagnostic note as an instance of the failure it
diagnoses. The present audit does not require adding Qin to the 51-paper corpus.

### 2. Boundary and accuracy directions require conditions

Al-Shami's Section 6 explicitly distinguishes operator properties from
approximation accuracy. Table 1 is a three-object worked example comparing
classes of sets. It does not evaluate held-out classification. The manuscript's
previous implication that every relaxation gives coarser granules and therefore
a smaller boundary was not justified by this source.

Wang & Ma's characterisations are conditional: for example, Theorem 2 in the
specified CRT space connects T1, discreteness and singleton neighbourhoods;
Theorem 3 connects regularity and a partition structure. These are not blanket
equivalences for arbitrary neighbourhood rough sets.

### 3. TDABC is not just its neighbour vertex set

The source's Eq. (10), visually checked on PDF p. 14 (printed p. 506), sums
label contributions over link/star simplices with filtration-value weights.
Passing to only the vertices discards simplex multiplicities and weights.
A vertex-neighbourhood correspondence therefore does not establish a
whole-classifier reduction. The paper has classifier baselines; no significance
test is reported in the inspected evaluation. The updated manuscript's
statement that all seven class-b papers report a significance test conflicts
with its own TDABC provenance entry and has been removed.

The journal version is volume 18 (2024), pp. 493-538, published online in 2023;
2021 identifies the earlier preprint, not the journal issue.

### 4. Complete scores must retain their extra terms

The method-level differences are substantive enough that a common dependency
component does not prove equal feature rankings:

- Zhang: dependencies initialise weights, followed by ANN refinement.
- Sun: mixed dependency/information/granularity score, aggregated across balls.
- GBFRS: dependency significance plus local consistency.
- LDFS: label-weighted fuzzy dependency plus feature discernibility.
- PFFL: weighted dependency significance plus label consistency.
- LRFS: local positive-region dependency with a labelled-sub-universe denominator.

These observations establish component reuse or adaptation, not the novelty
or superiority of each complete method. That stronger judgement would require
comparison with the respective predecessors and appropriate ablations.

### 5. IFT + wrapper is a combined-method contribution

Author clarification confirms that the wrapper is required for the combined
method. Therefore T4_09 is class b, and the survey does not demand that the
IFT criterion alone reproduce the whole pipeline's gains. The following
questions remain relevant to attribution and reproducibility, not to whether
using a wrapper constitutes a failure.

The formula page, PDF p. 6 (printed p. 11804), was visually checked. Eq. (9)
defines a change in the subbasis-difference measure; Definition 5.3 uses an
identity-base condition. Neither is visibly the standard positive-region
fraction. The survey supplies no derivation proving that the complete score
is a monotone transform of NRS dependency. Monotonicity under feature-set
inclusion would not suffice for that claim.

Results must also be attributed correctly. Tables 7 and 8 report mean F_IFT
accuracy of 72.68 and 71.21 versus all-features values 79.63 and 80.02,
respectively. Section 6.4 discusses wrapper improvement over F_IFT. Thus the
headline smaller-size and higher-accuracy figures cannot be combined into a
single result against dependency-based NRS. The source contains 14 numbered
tables, not 25.

Section 6.1 (p. 11814) describes repeated sampling, classification
cross-validation and repeated wrapper evaluation, but the inspected account
does not clearly identify an outer test split independent of wrapper choice.
This is a protocol-clarity concern. It is not proof of leakage or proof that
the method only wins on a self-aligned metric.

Questions for author adjudication:

1. Derive the exact connection, if any, between Eqs. (6)-(9) and a specified
   rough-set dependency under explicitly stated relations and thresholds.
2. Reconcile the direction of the significance increment in Eq. (9), the
   monotonicity statement in Proposition 5.3 and the maximisation in Algorithm 1.
   This is a question about the printed specification, not a verified code defect.
3. State whether feature selection, preprocessing and wrapper choice were
   repeated strictly inside training data for every reported test fold.
4. Identify the exact variant/comparator behind each percentage claim and
   report uncertainty or paired results if available.

## Source file map

Paths are relative to the workspace root. Original PDFs were not modified.

| ID | Local PDF |
|---|---|
| T2A_01 | AIR/coding/fulltext/1-s2.0-S0020025506001642-main.pdf |
| T2A_02 | AIR/coding/fulltext/1-s2.0-S0020025523001937-main.pdf |
| T2A_03 | AIR/coding/fulltext/Journal of Mathematics - 2025 - Al-Shami - Applications of  ‐Open Sets via Separation Axioms  Covering Properties  and.pdf |
| T2A_04 | AIR/coding/fulltext/CAAI Trans on Intel Tech - 2019 - Wang - Study on covering rough sets with topological methods.pdf |
| T2A_05 | AIR/coding/fulltext/1-s2.0-S0020025508004271-main.pdf |
| T2B_01 | AIR/coding/fulltext/s11634-023-00548-4.pdf |
| T4_09 | AIR/coding/fulltext/s00500-024-09910-w.pdf |
| T1_03 | Tire1/1-s2.0-S0893608025000577-main.pdf |
| T1_04 | Tire1/1-s2.0-S0952197625001915-main.pdf |
| T1_14 | AIR/coding/qian_fulltext/T1_14.pdf |
| T4_10 | AIR/coding/qian_fulltext/T4_10.pdf |
| T4_11 | AIR/coding/qian_fulltext/T4_11.pdf |
| T4_12 | AIR/coding/qian_fulltext/T4_12.pdf |

## Release boundary

Source availability is resolved. Claim adjudication is not fully resolved.
Keep the historical CSV intact until its interpretation fields can be updated
as a versioned dataset, reconcile the release documentation, and obtain author
confirmation of the IFT interpretation and the TDABC denominator choice.
Do not advertise the manuscript as submission-ready solely on this audit.
