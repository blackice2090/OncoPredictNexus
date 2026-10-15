# Research notebooks

These notebooks document **development experiments**, separate from the frozen Ridge artifact served by the application.

| Directory | Notebook | Question |
| --- | --- | --- |
| `ic50_notebook/` | `OncoPredict_IC50_EDA_Training.ipynb` | EDA, grouped nested evaluation, small feature engineering and bounded tuning. |
| `xgboost_comparison/` | `OncoPredict_XGBoost_Comparison.ipynb` | Bounded XGBoost comparison on the same frozen cell-grouped partitions. |

The public notebook copies retain the original scientific annotations, including Arabic research explanations, but remove cached cell outputs and machine-specific kernel registration. They have not been relabeled as improved deployed models. The small copied data snapshots and their SHA-256 manifests remain available alongside each notebook. Raw screening archives are excluded.

## Run a development notebook

Use a separate environment from the serving application:

```bash
python -m venv .venv-training
# Activate it using your shell.
python -m pip install -r training/ic50_notebook/requirements.txt
python -m pip install jupyterlab
python -m jupyter lab
```

For the algorithm comparison, also install the XGBoost version recorded in the original experiment (`3.4.1`) if it is not listed in your selected environment. Open the notebook from its own directory and run cells in order. Existing helper execution scripts may reference the original local project environment; Jupyter is the portable entrypoint for this release.

Running a notebook can create a new experimental run and take substantially longer than inference. It does **not** automatically replace `app/research_predictor/assets/exploratory_model.joblib`.

## Recorded outcomes

- IC50 notebook selection: RMSE **1.515600**, about **1.07% lower** than original Ridge; development criterion not met.
- XGBoost: RMSE **1.578359**, about **3.03% higher** than original Ridge; no replacement.

Both conditional difference intervals included zero. The development threshold was a project rule, not a medical standard. See [research scope](../docs/RESEARCH.md) and the original aggregate JSON records in `docs/evidence/`.
