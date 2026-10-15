# Research scope and evidence

## Original exploratory study

The approved analysis uses 83 independent NSCLC cell lines, 249 cell–drug targets, eight binary mutation-feature slots and three drugs: Osimertinib, Erlotinib and Gefitinib. Five of 88 cell lines lacked valid genomic linkage and were excluded. Rare EGFR variants are auxiliary features rather than independently validated evaluation groups.

The target is fitted **LN_IC50**. Displayed micromolar IC50 values are exponentiated model outputs. They are not treatment doses. Evaluation uses three repeats of five outer folds grouped by cell, with four inner folds for tuning. Every cell's three drug targets stay together.

| Original comparison | RMSE on LN_IC50 | Ranking agreement |
| --- | ---: | ---: |
| Drug-wise mean baseline | 1.682771 | 79.5% |
| Ridge | 1.531918 | 78.7% |
| Random Forest | 1.560913 | See the frozen study record |

Ridge reduced pooled numerical error by approximately 9% relative to the baseline as a descriptive comparison, while ranking agreement did not improve. Ranking agreement is not an individual confidence score. The evidence does not establish stable statistical superiority or clinical validity.

The full original summary is `app/research_predictor/assets/run_summary.json`. The runtime artifact's SHA-256 is `049a37d94c50aca766da3ce0e103cbcf5dbbb696474a8627bea6087cd04a0acb`.

## Target measurement limitation

218/249 fitted IC50 targets (87.6%) were above the highest tested dose. All raw-series viability points remained above 50% in 215 of these pairs. This restricts interpretation of numerical error outside the observed range. It does not prove that all fitted values are wrong, and the project did not automatically exclude flagged observations.

## Completed development findings

The targets and metrics below belong to different experiments and must not be pooled as one accuracy measure.

| Experiment | Primary finding | Interpretation |
| --- | --- | --- |
| Bounded IC50 target handling | RMSE about 0.675 versus 0.715 under the alternative metric | Development criteria not met; not directly comparable with original IC50 RMSE. |
| Viability at dose | MAE improvement about 4.71% | Primary criterion not met. |
| Influential-cell sensitivity | Mean gain fell to about 0.49% without the five largest contributions | Arithmetic diagnostic; no cells deleted or model retrained for that sensitivity calculation. |
| Replicate sensitivity | 17/100 primary choices reached a 5% improvement | Does not establish independent validation. |
| PRISM viability check | 31 new cells, mean improvement about 3.94% | Conditional difference interval included zero. |
| Three-gene expression addition | 75 shared cells, MAE increased about 1.50% | No sufficient benefit in this tested configuration; not a conclusion about expression generally. |
| PIK3CA addition | MAE increased about 0.58% | Addition not adopted. |
| gCSI viability check | Six new cells, two drugs, pooled mean gain about 6.19% | Conditional interval included zero; limited scope. |
| Viability algorithm family | Random Forest MAE increased about 0.33% versus Ridge | Did not justify replacement. |
| IC50 notebook selection | RMSE 1.515600, about 1.07% below original Ridge | Conditional interval included zero; development rule not met. |
| Bounded XGBoost IC50 comparison | RMSE 1.578359, about 3.03% above original Ridge | Conditional interval included zero; Ridge retained. |

The IC50 development rule required at least 5% RMSE reduction, a positive conditional difference interval, and no MAE increase. It is a project development rule, not a medical standard or a requirement for a functional software MVP. Conditional intervals based on saved predictions do not include uncertainty from retraining.

The notebook selection and XGBoost evidence are in `docs/evidence/`. PRISM and gCSI outcomes have become known to development. A later candidate informed by them needs a new untouched evaluation.

## Explainability

The deployed pipeline applies its original variance selector and Ridge coefficients. Exact interventional linear SHAP uses the 83 original training cells as background. The implementation checks that background prediction plus feature contributions reconstructs LN_IC50.

This is computational explanation, not biological causation. Correlation among EGFR flags limits isolated feature interpretation. Global explanations describe the model fitted on the full training data; they are not held-out feature-importance validation.

## TCGA example

The public sample **TCGA-95-7039-01**, from TCGA LUAD 2014, demonstrates source tracing and workflow execution:

| Gene | Reported protein call | Reference reads | Alternate reads |
| --- | --- | ---: | ---: |
| EGFR | p.S921R, encoded as Other_EGFR | 94 | 14 |
| TP53 | p.R273L | 7 | 18 |
| KRAS | p.D33E | 11 | 6 |

The mutation calls have not been independently or clinically confirmed by this project. The KRAS call has only 17 reported reads. The example does not certify sequencing quality, establish S921R-specific response, or include matched drug-response labels. Transfer from laboratory cell lines to patient tissue remains unvalidated.

Source identity, pinned cBioPortal DataHub commit and scope are preserved in `app/research_predictor/assets/tcga_demo_proxy.json`.

## Next research evidence

Define a justified policy for targets outside the tested range. Secure new compatible response measurements and feature coverage. Freeze the candidate, preprocessing, endpoint and evaluation criteria before viewing the new outcomes. Review per-drug error, uncertainty and coverage together. Evaluate research-user usability separately from predictive validity.
