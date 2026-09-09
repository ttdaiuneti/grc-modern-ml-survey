# When Modern Mathematics Meets Granular Computing — data and code

Reproducibility package for the survey *When Modern Mathematics Meets Granular
Computing: A Critical Survey of What Works, What Fails, and Why*
(Thanh Dai Tran, Long Giang Nguyen).

Every number printed in the paper is derived from the CSV files in `data/` by
the scripts in `code/`. Nothing is transcribed by hand. The scripts in
`code/audit/` exist so that a reader can check that claim rather than take it
on trust.

## Layout

```
data/         raw measurements + review artefacts (the single source of truth)
code/
  experiments/  produce the raw CSVs from the UCI datasets
  analysis/     turn raw CSVs into the paper's tables and figures
  audit/        re-derive every printed number and re-resolve every citation
manuscript/   LaTeX source, so the audit scripts have something to check
requirements.txt
```

## Quick start

```bash
pip install -r requirements.txt

# 1. Regenerate every table in the paper from the raw data
python3 code/analysis/gen_tables.py          # writes manuscript/tables/*.tex

# 2. Check the manuscript against the raw data
python3 code/audit/verify_tables.py          # exit 0 = every number checks out

# 3. Check every reference resolves and points at the right paper
python3 code/audit/check_dois.py             # needs network (Crossref)
python3 code/audit/check_authors.py          # needs network (Crossref)
```

```bash
# 4. Rebuild the PDF (needs XeLaTeX; the package carries the class files)
cd manuscript && latexmk -xelatex main.tex
```

`verify_tables.py` regenerates the tables into a temporary copy, diffs them
against the committed ones, recomputes the inline statistics quoted in the
prose, and fails if any of them has drifted. It also asserts that claims the
paper explicitly retracted during revision have not crept back in.

## Reproducing the experiments from scratch

The raw CSVs are committed, so none of this is required to check the paper.
To regenerate them (hours, not minutes — persistence computation dominates):

```bash
cd code/experiments
python3 run_e1.py            # -> raw_importance.csv, raw_downstream.csv
python3 run_structure.py     # -> raw_structure.csv
python3 run_knn_scale.py     # -> raw_knn_scale.csv   (needs raw_structure.csv)
```

Datasets are fetched by `datasets.py` from `sklearn` and the UCI repository,
standardised (z-score) and capped at n ≤ 600. Set `GRC_DATA` to redirect where
the scripts look for the CSVs.

## What is in `data/`

| File | Rows | Contents |
|---|---|---|
| `raw_importance.csv` | 4,975 | Attribute importance per (dataset, method, attribute, seed). One 80% subsample **without replacement** per seed — not a bootstrap. `pai_bound` stores (d_max+1)·range(a_j), the bound for the summed PAI score. |
| `raw_downstream.csv` | 30,100 | Top-k accuracy per (dataset, method, k, seed, fold). Importance is recomputed inside each training fold, so no test object influences the selection later evaluated on it. |
| `raw_structure.csv` | 995 | Structure-preservation metrics per (dataset, method, k). Single-shot: no seed column, no replication — the paper's tests are dataset-level for this reason. |
| `raw_knn_scale.csv` | 5,970 | `knn_overlap` and `trustworthiness` recomputed over K ∈ {3,5,10,20,30,50} on the *same* feature subsets, to test whether the metric's own scale parameter decides the verdict. |
| `literature_log.csv` | 52 | Systematic-review log. `read_level` is `abstract` for all entries; see the paper's Appendix A for what that does and does not support. |
| `fulltext_coding.csv` | 22 | Reporting-practice coding of papers read at full text. Every cell carries the quotation it rests on in the `evidence` column, so an individual judgement can be overturned without re-reading the paper. |

## Known limitations recorded here rather than hidden

- `literature_log.csv` row `T1_24` lost three free-text fields
  (`relevance`, `key_claim`, `key_finding`) to a file-write error during
  revision. The bibliographic fields were re-verified against OpenAlex. The
  gap is marked in that row's `notes`.
- `fulltext_coding.csv` is a convenience sample limited by full-text
  availability. Thirteen of its 22 papers belong to the survey's Axis-1
  corpus; the figures generalise to Axis 1, not to Axes 2–4.
- Three bibliography entries (`Adams2017persistence`, `Zheng2021grouping`,
  `Zhang2022PWS`) still use `and others` because JMLR and IJCAI do not
  register DOIs with Crossref, so author lists could not be completed
  automatically.

## Licence

`code/` and `manuscript/` are MIT-licensed (see `LICENSE`).
`data/` is licensed under CC BY 4.0 (see `DATA_LICENSE`) — cite the paper
when reusing the released measurements or the literature-review log.
The UCI datasets themselves are redistributed under their original terms;
only derived measurements are committed here.

## Citation

Citation details will be added once the paper is accepted.

```
Tran, T.D. and Nguyen, L.G. When Modern Mathematics Meets Granular Computing:
A Critical Survey of What Works, What Fails, and Why. (Manuscript.)
Code and data: https://github.com/ttdaiuneti/grc-modern-ml-survey
```
