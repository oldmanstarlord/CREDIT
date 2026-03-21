"""CLI entrypoint to run the complete standalone ML workflow."""

import argparse
import json
from pathlib import Path
from typing import Dict

from .config import GMSC_FEATURES, HOME_CREDIT_FEATURES, PipelineConfig
from .data_sources import (
    load_gmsc_train,
    load_home_credit_train,
    load_installments,
    load_mytransaction,
    load_previous_applications,
)
from .fairness import run_fairness_audit
from .feature_engineering import (
    aggregate_installments,
    aggregate_previous_applications,
    engineer_gmsc_features,
    engineer_home_credit_features,
    extract_transaction_features,
)
from .modeling import train_full_pipeline


def _save_json(path: Path, payload: Dict) -> None:
    """Write dictionary payload to disk as pretty JSON."""
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def run_gmsc_pipeline(config: PipelineConfig) -> Dict:
    """Train model on Give Me Some Credit dataset with engineered features."""
    df = load_gmsc_train(config)
    df = engineer_gmsc_features(df)
    result = train_full_pipeline(df, "SeriousDlqin2yrs", GMSC_FEATURES, config)

    tx_df = load_mytransaction(config)
    tx_features = extract_transaction_features(tx_df)
    tx_file = config.output_dir / f"transaction_features_{result['artifact']['model_version']}.json"
    _save_json(tx_file, tx_features)
    result["transaction_features_file"] = str(tx_file)
    return result


def run_home_credit_pipeline(config: PipelineConfig) -> Dict:
    """Train model on Home Credit application_train with optional aggregates."""
    df = load_home_credit_train(config)
    df = engineer_home_credit_features(df)

    installments = load_installments(config)
    if installments is not None:
        inst_agg = aggregate_installments(installments)
        df = df.merge(inst_agg, on="SK_ID_CURR", how="left")

    prev = load_previous_applications(config)
    if prev is not None:
        prev_agg = aggregate_previous_applications(prev)
        df = df.merge(prev_agg, on="SK_ID_CURR", how="left")

    target = "TARGET"
    features = [f for f in HOME_CREDIT_FEATURES if f in df.columns]
    result = train_full_pipeline(df.fillna(0), target, features, config)

    sensitive_cols = [c for c in ["CODE_GENDER", "NAME_EDUCATION_TYPE", "NAME_INCOME_TYPE"] if c in df.columns]
    if sensitive_cols:
        fairness = run_fairness_audit(
            result["artifact"]["model"],
            result["X_test"],
            df.loc[result["X_test"].index, sensitive_cols],
            result["artifact"]["threshold"],
        )
        fairness_file = config.output_dir / f"fairness_{result['artifact']['model_version']}.json"
        _save_json(fairness_file, fairness)
        result["fairness_file"] = str(fairness_file)
    return result


def main() -> None:
    """Run selected pipeline from CLI."""
    parser = argparse.ArgumentParser(description="Run Barclays standalone ML training pipeline")
    parser.add_argument(
        "--dataset",
        choices=["gmsc", "home_credit"],
        default="gmsc",
        help="Dataset to train on first",
    )
    args = parser.parse_args()

    config = PipelineConfig()
    if args.dataset == "gmsc":
        result = run_gmsc_pipeline(config)
    else:
        result = run_home_credit_pipeline(config)

    summary = {
        "dataset": args.dataset,
        "model_version": result["artifact"]["model_version"],
        "model_file": result["model_file"],
        "metrics_file": result["metrics_file"],
        "shap_file": result["shap_file"],
        "threshold": result["artifact"]["threshold"],
        "metrics": result["artifact"]["metrics"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
