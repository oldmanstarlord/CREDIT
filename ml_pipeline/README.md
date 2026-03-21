# Standalone ML Pipeline

This ML pipeline is intentionally standalone so you can optimize model quality before backend/frontend integration.

## Scope

- Data loading from canonical workspace dataset layout
- Dataset-specific cleaning (GMSC, Home Credit, MyTransaction)
- Feature engineering with financial rationale
- Model training (Logistic, RandomForest, XGBoost)
- Imbalance strategy selection (class weight vs SMOTE)
- Threshold tuning (F2-oriented)
- SHAP global feature importance
- Fairness audit (Home Credit sensitive groups for monitoring only)
- Artifact generation for later API integration

## Canonical Dataset Location

The pipeline expects raw files under:

- `../datasets/raw`

Configured datasets:

- `give-me-some-credit/cs-training.csv`
- `home-credit/application_train.csv`
- `my-transaction/MyTransaction.csv`

## Run Training

From project root:

```bash
python -m ml_pipeline.run_training --dataset gmsc
python -m ml_pipeline.run_training --dataset home_credit
```

## Outputs

Artifacts are written to:

- `ml_pipeline/models/credit_model_<version>.pkl`
- `ml_pipeline/models/metrics_<version>.json`
- `ml_pipeline/models/shap_top_<version>.json`
- `ml_pipeline/models/fairness_<version>.json` (Home Credit)
- `ml_pipeline/models/transaction_features_<version>.json` (GMSC run)

## Integration Plan Later

Once model quality is accepted, wire artifacts into backend scorer service:

- `backend/app/ml/predict.py`
- `backend/app/services/scoring_service.py`
- `backend/app/api/routes/scoring.py`
