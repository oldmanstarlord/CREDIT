# ML Data Directory Policy

This folder is reserved for pipeline-generated artifacts only:

- cleaned/intermediate datasets
- train/validation splits
- feature tables for experiments

Do not place raw source datasets here.

Raw source datasets live in the workspace-level folder:

- `../../datasets/raw`
- archives in `../../datasets/archives`

Canonical path helpers are provided in:

- `backend/app/ml/dataset_paths.py`
