# Claim-level coding of the 51-paper corpus

## Status and authoritative files

The screening inventory is maintained in `failure_pattern_coding.csv`:
51 records, with 13 labelled import, 23 internal and 15 background.
The source-level correction ledger is [FULLTEXT_EVIDENCE_REVIEW.md](FULLTEXT_EVIDENCE_REVIEW.md).
Its interpretations supersede the legacy `pattern`, rationale and provenance
statements where they conflict. The CSV is retained as a historical screening
record, not a validated failure-prevalence dataset. T4_09 was corrected after
author clarification: FW_IFT is a combined IFT--wrapper method. Do not use legacy
labels to count failed methods.

The present audit examined selected contribution, definition, algorithm and
results passages in the full-text PDFs. It is an assistant-assisted source
review, not independent human double coding, an exhaustive proof check or an
experimental replication. Author adjudication remains required; no agreement
statistic is claimed.

## Screening scope

The existing import label includes abstract/fuzzy topology, weak supervision,
neural components and TDA. It is broader than an actual import into the entire
neighbourhood-approximation-reduct pipeline: Kindelan's TDABC is a classifier
without rough-set reducts. Keep this comparison case identifiable. Do not infer
that all 13 methods reuse NRS dependency.

## Descriptive claim classes

| Class | Meaning | Records |
|---|---|---:|
| a | Theoretical characterisation or equivalence study, without a classification experiment | 5 |
| b | Methodological adaptation reporting baseline comparisons | 8 |

The former 5/7/1 split is superseded by 5/8: T4_09 belongs in class b.
Its need for wrapper search is part of the method, not a failure. This
clarification does not establish the isolated criterion's incremental value
or validate the train/test protocol. Class b does not require a
significance test: TDABC reports baseline comparisons but no such test.
Absence of experiments does not by itself demonstrate mathematical novelty
or correctness. Presence of a baseline or test does not establish an adequate
protocol. These are separate evidence fields.

Class a: T2A_01, T2A_02, T2A_03, T2A_04, T2A_05.
Class b: T1_03, T1_04, T1_14, T4_10, T4_11, T4_12, T2B_01, T4_09.

Genre composition: five theoretical topology studies, four Qian-group
weak-supervision studies, two Axis-1 methods, one TDA classifier and one IFT
self-citation. The six Axis-2a records include the empirical IFT paper; they
are not six papers without classification experiments.

## Evidence rules

1. Record the exact target of a criticism. Zhang (2009) diagnoses Qin (2008);
   that diagnosis is not a failure of Zhang's note.
2. Distinguish an identity, a restricted correspondence, component reuse and
   a loose analogy. A shared bound or monotonicity in feature inclusion is
   not proof of a monotone transformation of NRS dependency.
3. Preserve additional score terms and learned stages. Reducing one component
   does not reduce a sum, product, learned weighting or complete classifier.
4. Attribute empirical gains to the correct variant, comparator and metric.
   Approximation accuracy is not classifier accuracy. The IFT filter and
   wrapper cannot share an undifferentiated 50%/10% claim against NRS.
5. Missing significance testing is a reporting limitation, not Pattern C.
   Selection leakage needs direct protocol or code evidence, not speculation.
6. Use unresolved when the required proof or protocol evidence is absent.

## Remaining work before freezing the release

- T4_09 is class b. The ledger's component-attribution and protocol questions
  remain limitations, not an adverse classification.
- Decide whether TDABC belongs in the import denominator or a separate comparison stratum.
- Reconcile the historical CSV rationale/pattern fields with the adjudicated ledger
  in a versioned data update. Do not silently overwrite the original screening history.
- Synchronise the release package and disclose the actual assistance and human
  verification used. Availability of all PDFs alone does not close these steps.
