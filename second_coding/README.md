# Independent second coding of the 13 cross-framework papers (Reviewer 2, comment 4)

**For:** a co-author who did not do the first coding (Long Giang Nguyen or Nam S. Vo).
**Time needed:** about 3–5 hours (13 papers; only the experimental section and the
contribution statement of each paper need to be read closely).

## What to do

1. Do **not** open `../coding/failure_pattern_coding.csv`, `../coding/FULLTEXT_EVIDENCE_REVIEW.md`
   or Section 7.4 of the manuscript before you finish. The coding must be blind.
2. Read each paper in `coding_sheet_coder2.csv` at full text. PDFs: `fulltext/` and `fulltext/qian_fulltext/`
   (some files are named by publisher ID; match by journal, volume and page).
   The PDFs are publisher copies and are not part of this release; obtain them from the publishers.
3. Fill in, for each paper:

| Column | Values | Rule |
|---|---|---|
| `classification_experiment` | `yes` / `no` | Does the paper report a classification (or feature-selection) experiment on data? A worked numerical example of set approximation does **not** count. |
| `baseline_comparison` | `yes` / `no` | Does it compare its method with at least one other method on the same data and metric? |
| `significance_test` | `yes` / `no` | Is a named statistical test carried out on the paper's own results? Citing a test does not count. |
| `claim_class` | `a` / `b` | **a** = theoretical characterisation or equivalence study, with no classification experiment. **b** = methodological adaptation that reports baseline comparisons (a significance test is not required). |
| `evidence_quote` | text | A short quotation or a pointer (section, table, page) that supports your `claim_class`. |
| `notes` | text | Anything unclear. Use `unresolved` in `claim_class` if the paper does not let you decide. |

4. Save the file and send it back. Do not change the first three columns.

## After both codings exist

```bash
python3 agreement.py coding_sheet_coder2.csv
```
prints the per-field agreement, Cohen's kappa and every disagreement. Disagreements are
resolved by discussion between the two coders; the resolution and its reason are written
into `reconciliation.md`. The manuscript then reports: who coded, that coding was blind,
the agreement before discussion, and how disagreements were resolved.

## Note on the coding key
The T1_14 key inconsistency (`Sun2023KBS` for a paper by Qian et al.) was resolved
after the second coding: the key is now `Qian2023KBSldl` (see `reconciliation.md`).
