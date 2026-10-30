# Reconciliation of the two claim-class codings (13 cross-framework papers)

**Coder 1:** T.D.T. (first coding, `../coding/failure_pattern_coding.csv`; every assignment was
checked against the PDF).
**Coder 2:** N.S.V., blind to coder 1's labels (`coding_sheet_coder2.csv`, received 24 October 2026).
**Comparison:** `python3 agreement.py coding_sheet_coder2.csv`

## Result

| Field | Agreement |
|---|---|
| `claim_class` (a / b) | 13 of 13 papers; Cohen's kappa = 1.00 |

No paper received different classes, so no disagreement had to be resolved.
With 13 papers and two classes, kappa is imprecise; it describes this exercise only.

| Class | Papers |
|---|---|
| a (theoretical characterisation or equivalence, no classification experiment) | T2A_01 Zhu 2007, T2A_02 Yao W. 2023, T2A_03 Al-shami 2025, T2A_04 Wang Xue 2019, T2A_05 Zhang 2009 |
| b (methodological adaptation with baseline comparisons) | T1_03 Zhang 2025, T1_04 Sun 2025, T1_14 Qian W. 2023, T4_09 Dai T.T. 2024, T2B_01 Kindelan (TDABC), T4_10 Qian W. 2024, T4_11 Qian W. 2022, T4_12 Qian W. 2023 |

## Coder 2's other fields, checked against the manuscript

Coder 2 also recorded `classification_experiment`, `baseline_comparison` and `significance_test`.
These were not part of coder 1's sheet, so no agreement statistic is computed for them. They were
checked against what the manuscript states about each paper:

| Paper | Coder 2 | Manuscript | Consistent |
|---|---|---|---|
| T1_03 Zhang 2025, T1_04 Sun 2025 | Friedman + Nemenyi run | Appendix A: "Both report ... a Friedman test with a Nemenyi post-hoc" | yes |
| T2B_01 Kindelan | 8 datasets; KNN, weighted KNN, linear SVM, RF; no named test | Section 4.2: eight datasets, outperforms k-NN and weighted k-NN; Appendix A: four baseline classifiers, no significance test | yes |
| T4_09 Dai 2024 (IFT) | baselines; no named test | Section 4.1: "confirming the margin would need dispersion or significance tests" | yes |
| T2A_02, T2A_03 | "No data was used" / "No data were used" | class (a): no classification experiment | yes |
| T1_03, T1_04 (also in the 22-paper reporting-practice coding) | significance_test = yes | `fulltext_coding.csv`: significance_test = 1 for both | yes |

## Corrections made because of coder 2's evidence

1. **Reporting-practice coding, FT_16 (Sun 2025, EAAI).** Coder 2's evidence for T1_04 cites a
   comparison of GRFSL with "OMDP" in Table 4. In the PDF (Sec. 5.2), OMDP is "the original multilabel
   data processing", i.e. the unreduced data, evaluated with MLKNN on all 14 datasets. The rule of
   `all_features_baseline` ("a classification result on the unreduced attribute set") is met, but
   `fulltext_coding.csv` had 0. Corrected to 1 (both copies), with the evidence quoted in the row.
   Consequences, all regenerated or re-audited: Table `tab:practice` 5/22 → 6/22 and 3/13 → 4/13;
   Table `tab:practice_detail` row T1_04; Section 8.1 "17 of the 22 ... 10 of the 13" → 16 / 9;
   Section 8.2 "10 of 13" → 9 of 13; Table `tab:standard` 5 of 22 → 6 of 22. "No paper reports all
   four practices" still holds (Sun 2025 reports no dispersion).
2. **Bibliography key.** Coder 2 noted that T1_14 is labelled `Sun2023KBS` although the PDF is by
   Wenbin Qian et al. (KBS 278, 2023, 110898). The printed citation was already correct (the key is
   internal); the key is renamed `Qian2023KBSldl` in `refs.bib`, Sections 3 and 6 and the coding CSV.
   Coder 2's sheet is kept unchanged as received.
3. **Kindelan et al.** Coder 2 records the journal version as Advances in Data Analysis and
   Classification 18 (2024) 493–538. The manuscript already prints 2024; the internal label
   "Kindelan 2021" in the coding files is a legacy identifier only.

## Later re-check of the reporting-practice coding (24 October 2026)

Prompted by correction 1, every cell of `fulltext_coding.csv` was re-checked against the full
texts, including page images of result tables that are not in the PDF text layer. Eleven more
cells in ten papers were corrected, all practices that had been coded as absent: baseline
(FT_01, FT_07, FT_21), dispersion (FT_01, FT_02, FT_10, FT_11, FT_12, FT_19), test (FT_06),
ablation (FT_04), and one false positive corrected 1 -> 0: ablation (FT_18). Evidence per cell: `../coding/fulltext_recheck_2026-10-24.md`. The counts quoted
in correction 1 above are superseded: 13/22 and 7/13 papers now omit the all-features baseline.
