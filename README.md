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
requirements.txt
```

The LaTeX manuscript is kept separately and is not part of this repository.
The `audit/` scripts that read the paper source (`verify_tables.py`,
`check_dois.py`, `check_authors.py`) look for it at `GRC_MANUSCRIPT`; point
that at a local checkout of the manuscript to run them.

## Quick start

```bash
pip install -r requirements.txt

# 1. Regenerate every table in the paper from the raw data
python3 code/analysis/gen_tables.py          # writes tables/*.tex in the CWD

# 2. Check the paper's numbers against the raw data (needs GRC_MANUSCRIPT)
python3 code/audit/verify_tables.py          # exit 0 = every number checks out

# 3. Check every reference resolves and points at the right paper
python3 code/audit/check_dois.py             # needs network (Crossref) + GRC_MANUSCRIPT
python3 code/audit/check_authors.py          # needs network (Crossref) + GRC_MANUSCRIPT
```

`verify_tables.py` regenerates the tables into a temporary copy, diffs them
against the ones in the manuscript checkout, recomputes the inline statistics quoted in the
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
| `literature_log.csv` | 51 | Systematic-review log. `read_level` is `abstract` for all entries; see the paper's Appendix A for what that does and does not support. |
| `fulltext_coding.csv` | 22 | Reporting-practice coding of papers read at full text. Every cell carries the quotation it rests on in the `evidence` column, so an individual judgement can be overturned without re-reading the paper. |

## Known limitations recorded here rather than hidden

- One paper (Yao 2016, "A triarchic theory of granular computing") was
  originally logged as an included, systematically-reviewed paper, but its
  review-log fields (`relevance`, `key_claim`, `key_finding`) were lost to a
  file-write error during revision and could not be reconstructed. Rather
  than keep an incomplete row, it was removed from the 52-paper corpus and
  reclassified as one of the background/foundational references it is cited
  as in the manuscript; the corpus count was updated to 51 throughout
  (Appendix A). The citation itself remains, with a verified DOI.
- `fulltext_coding.csv` is a convenience sample limited by full-text
  availability. Thirteen of its 22 papers belong to the survey's Axis-1
  corpus; the figures generalise to Axis 1, not to Axes 2–4.
- `Adams2017persistence` (a JMLR paper with no DOI registered anywhere) was
  removed from the bibliography rather than kept unverifiable; the sentence
  citing it was rewritten to fold its content into the adjacent survey
  citation. `Zheng2021grouping` and `Zhang2022PWS` turned out to have real
  DOIs after all (Crossref's bibliographic search missed them on the first
  pass; `Zhang2022PWS`'s DOI is a DataCite/arXiv one, not indexed by
  Crossref, and is verified by a direct `doi.org` redirect instead) — both
  now carry complete author lists and correct metadata.

## Licence

`code/` is MIT-licensed (see `LICENSE`).
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
