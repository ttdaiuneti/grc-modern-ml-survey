# Re-check of the reporting-practice coding (22 papers) against the full texts — 24 Oct 2026

Source PDFs: research-commons paper store (all 22 available). Method: text layer (`pdftotext -layout`)
for every paper; page images for the nine papers whose result tables are not in the text layer
(FT_01, 02, 11, 12, 17, 18, 19, 20, 21) and for any cell where the text was ambiguous.
Coding rules as in Appendix A (presence only).

## Cells that disagree with the original `fulltext_coding.csv` (12 cells, 11 papers; 11 omissions 0 -> 1, one false positive 1 -> 0)

| ID | Paper (store) | Item | Coded | Found | Evidence |
|---|---|---|---|---|---|
| FT_01 | Xia 2020 TKDE GBNRS (L28) | baseline | 0 | 1 | p. 1238 Table 2 has an "original" column (accuracy on the unreduced data) next to NRS, FARNeMF, GBNRS, MGBNRS |
| FT_01 | same | dispersion | 0 | 1 | Table 2 entries are mean±sd; text: "the classification accuracies with variances are presented" |
| FT_02 | Xia 2023 TNNLS GBRS (L29) | dispersion | 0 | 1 | Tables II and III (pp. 1730–1731) give mean±sd for every method |
| FT_04 | Ji 2023 INS FGBERS (L22) | ablation | 0 | 1 | Fig. 4 "Relationships between classification accuracy and purity threshold for different datasets" (threshold 0.55–0.95) |
| FT_06 | Li 2023 IJAR (L25) | test | 0 | 1 | "the paired t test (significance level p = 0.05) is used to reflect the significant differences" |
| FT_07 | Xu 2022 CIS 8:287 (L30) | baseline | 0 | 1 | Tables 8, 9, 12–14: column "Original" = accuracy on the unreduced data (KNN, CART, C4.5) |
| FT_10 | Xia 2025 TFS GBFRS (L26) | dispersion | 0 | 1 | Table II (results) entries are "0.9500 ±0", "0.7871 ±0.7888", … (the ± is in the result table, not only in formulas) |
| FT_11 | Ding 2021 TETCI CFAOR (L124) | dispersion | 0 | 1 | Table III "(Test ± Std /%)", every entry mean ± sd |
| FT_12 | Xie 2024 TETCI GBG++ (L27) | dispersion | 0 | 1 | Table II "Mean ± Sd" for every classifier |
| FT_19 | Sun 2024 TFS GBFSO (L07) | dispersion | 0 | 1 | Tables III–IV: "average HV (HVA) and the standard deviation of HV (HVS)", SPA/SPS likewise |
| FT_21 | Xia 2024 TFS MGFE (L09) | baseline | 0 | 1 | Figs. 6–7: "the red dotted line represents the classification accuracy of the raw data on the specified classifier" (figure only; no number in a table) |
| FT_18 | Xia 2022 TNNLS efficient adaptive GB (L06) | ablation | 1 | 0 | The purity grid 0.54–1.0 tunes the existing GB method used for comparison and only its best result is reported (Tables V–VIII: "the GBS's highest average test accuracy"); the proposed method is adaptive with no purity parameter. Found when the coding rules were written into Appendix A (second pass, same day) |

## Cells confirmed (selection)
- FT_03, FT_06, FT_09, FT_10, FT_13, FT_15, FT_22: accuracy-table headers list only the compared methods (no unreduced column) -> baseline 0 confirmed.
- FT_18: Table II has mean and max, no sd -> dispersion 0 confirmed; kNN on the raw data -> baseline 1 confirmed.
- FT_17, FT_20: no sd, FT_20 no test -> confirmed. FT_11: no named test ("significantly best" mark only) -> test 0 confirmed.
- FT_02, FT_03, FT_10: own parameter tuned on a grid, only the best setting reported -> ablation 0 confirmed. FT_05: beta tuned 0.6–1, no per-value result -> 0 confirmed.

## Judgement calls (settled by the author, 24 Oct 2026)
1. FT_21 baseline shown only as a line in a figure: counts (rule: table or figure).
2. FT_19 sd of a multi-objective metric (HV, SP): counts (rule: any reported performance measure).
3. Papers that are not attribute-selection methods: FT_18 reduces objects and reports kNN on the raw data, so baseline 1; FT_12, FT_17, FT_20 are classifiers with no reduction step, so the item does not apply and is coded 0.

## Effect on the counts (all corrections applied)
| Item | All 22 (now -> new) | Axis-1 corpus 13 (now -> new) |
|---|---|---|
| All-features baseline | 6 -> 9 | 4 -> 6 |
| Dispersion | 6 -> 12 | 2 -> 5 |
| Significance test | 12 -> 13 | 7 -> 7 |
| Own-hyperparameter ablation | 7 -> 7 | 3 -> 2 |
| All four | 0 -> 0 | 0 -> 0 |
| None of the four | 5 -> 2 | 3 -> 2 |

## Coding rules as fixed in Appendix A after this re-check
- Baseline: a result without the paper's own reduction step, in a table or as a reference line in a figure. Methods that reduce objects: a result on the unreduced data counts. Classifiers with no reduction: item does not apply, coded 0.
- Dispersion: sd or per-fold values alongside a mean, for accuracy or any other reported performance measure.
- Test: a named test on the paper's own results; a significance mark without a named test does not count.
- Ablation: results at more than one value of a hyperparameter of the paper's own method; grid tuning with only the best setting reported does not count.

## Confirmation by the coder (T.D.T.)
T.D.T. checked each cell against the page given in the first table above and the Appendix A rule, and confirmed all thirteen on 30 October 2026. No code changed.

| # | Cell | Item | Now coded | T.D.T. (Y/N) | Date | Note |
|---|---|---|---|---|---|---|
| 1 | FT_01 Xia 2020 TKDE | baseline | 1 | Y | 2026-10-30 | |
| 2 | FT_01 Xia 2020 TKDE | dispersion | 1 | Y | 2026-10-30 | |
| 3 | FT_02 Xia 2025 TNNLS (GBRS) | dispersion | 1 | Y | 2026-10-30 | |
| 4 | FT_04 Ji 2023 INS | ablation | 1 | Y | 2026-10-30 | |
| 5 | FT_06 Li 2023 IJAR | test | 1 | Y | 2026-10-30 | |
| 6 | FT_07 Xu 2022 CIS | baseline | 1 | Y | 2026-10-30 | |
| 7 | FT_10 Xia 2025 TFS | dispersion | 1 | Y | 2026-10-30 | |
| 8 | FT_11 Ding 2021 TETCI | dispersion | 1 | Y | 2026-10-30 | |
| 9 | FT_12 Xie 2024 TETCI | dispersion | 1 | Y | 2026-10-30 | |
| 10 | FT_19 Sun 2024 TFS | dispersion | 1 | Y | 2026-10-30 | |
| 11 | FT_21 Xia 2024 TFS | baseline | 1 | Y | 2026-10-30 | |
| 12 | FT_18 Xia 2024 TNNLS | ablation | 0 | Y | 2026-10-30 | |
| 13 | FT_16 Sun 2025 EAAI | baseline | 1 | Y | 2026-10-30 | |

Cell 13 was corrected earlier from the second coder's evidence (second_coding/reconciliation.md, item 1); its source is Sec. 5.2 and Table 4 of the paper.
