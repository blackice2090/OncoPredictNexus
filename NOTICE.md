# Sources, attribution and reuse

This repository publishes project code, selected research notebooks, a frozen model artifact, small derived runtime snapshots, aggregate evidence and authentic interface screenshots. It does not include the synced project source collection, raw screening archives, private files, model-development environments, visitor experiment records, credentials or local Vercel configuration.

## Scientific data sources

- **Sanger / GDSC:** [drug-sensitivity documentation](https://depmap.sanger.ac.uk/documentation/datasets/drug-sensitivity/) describes fitted targets, assay conditions and normalization. Runtime derivatives retain source hashes in `app/research_predictor/assets/manifest.json`.
- **Broad DepMap / PRISM 20Q2:** [original dataset record](https://figshare.com/articles/dataset/PRISM_Repurposing_20Q2_Dataset/20564034). Used in a separate viability experiment; raw PRISM screens are not redistributed here.
- **gCSI / ORCESTRA:** [dataset record](https://www.orcestra.ca/pset/10.5281/zenodo.7829857). Used in a separate viability check; raw gCSI data are not redistributed here.
- **TCGA LUAD 2014:** [NCI/GDC study page](https://gdc.cancer.gov/about-data/publications/luad_2014), with public mutation calls taken from a [pinned cBioPortal DataHub snapshot](https://github.com/cBioPortal/datahub/tree/86690e1ed9752b1dcd50b5657f5f05eafa4b6b78/public/luad_tcga_pub). The runtime contains a small, attributed provenance demonstration rather than a patient-response dataset.
- **SHAP:** [LinearExplainer documentation](https://shap.readthedocs.io/en/latest/generated/shap.LinearExplainer.html) describes the computational interpretation used by the project.

Underlying datasets, software and third-party assets retain their respective terms. A link or runtime snapshot does not relicense a source dataset or imply endorsement of this project.

## Fonts and dependencies

The interface serves its font files locally. Their accompanying license files are retained under `app/research_predictor/frontend/public/fonts/`. Python and JavaScript dependencies retain their own licenses and are installed separately rather than vendored into this repository.

## Project code licensing

No project-wide open-source license has been selected by the repository owner in this release. Publishing the repository does not grant a new blanket license for its code, data derivatives or research content. Contact the owner before reuse beyond permissions otherwise provided by applicable terms.

This is a research prototype. It is not a clinically validated treatment-selection system.
