"""Model training and evaluation orchestration for dataset-first ML workflow."""

import json
import pickle
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import shap
from imblearn.over_sampling import SMOTE
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from .config import PipelineConfig


def _split_data(
    df: pd.DataFrame,
    target: str,
    features: List[str],
    config: PipelineConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Split into train/val/test with stratification for class imbalance."""
    X = df[features].fillna(0)
    y = df[target]

    X_temp, X_test, y_temp, y_test = train_test_split(
        X,
        y,
        test_size=config.test_size,
        random_state=config.random_state,
        stratify=y,
    )
    val_ratio_adjusted = config.val_size / (1 - config.test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp,
        y_temp,
        test_size=val_ratio_adjusted,
        random_state=config.random_state,
        stratify=y_temp,
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def _fit_baselines(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    random_state: int,
) -> Dict[str, float]:
    """Train logistic and random-forest baselines on validation split."""
    metrics: Dict[str, float] = {}

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    lr = LogisticRegression(
        class_weight="balanced",
        max_iter=1200,
        random_state=random_state,
        C=0.1,
    )
    lr.fit(X_train_scaled, y_train)
    lr_probs = lr.predict_proba(X_val_scaled)[:, 1]
    metrics["logistic_auc"] = float(roc_auc_score(y_val, lr_probs))

    rf = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced",
        max_depth=8,
        min_samples_leaf=50,
        n_jobs=-1,
        random_state=random_state,
    )
    rf.fit(X_train, y_train)
    rf_probs = rf.predict_proba(X_val)[:, 1]
    metrics["random_forest_auc"] = float(roc_auc_score(y_val, rf_probs))
    return metrics


def _fit_xgb_candidates(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    random_state: int,
) -> Tuple[XGBClassifier, str, Dict[str, float]]:
    """Compare class-weight and SMOTE variants and select better XGBoost model."""
    scores: Dict[str, float] = {}

    scale_pos_weight = (y_train == 0).sum() / max((y_train == 1).sum(), 1)
    weighted = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        eval_metric="auc",
        random_state=random_state,
        n_jobs=-1,
    )
    weighted.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    weighted_probs = weighted.predict_proba(X_val)[:, 1]
    scores["xgb_class_weight_auc"] = float(roc_auc_score(y_val, weighted_probs))

    smote = SMOTE(random_state=random_state, sampling_strategy=0.3)
    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
    smote_model = XGBClassifier(
        n_estimators=500,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="auc",
        random_state=random_state,
        n_jobs=-1,
    )
    smote_model.fit(X_train_smote, y_train_smote, verbose=False)
    smote_probs = smote_model.predict_proba(X_val)[:, 1]
    scores["xgb_smote_auc"] = float(roc_auc_score(y_val, smote_probs))

    if scores["xgb_class_weight_auc"] >= scores["xgb_smote_auc"]:
        return weighted, "class_weight", scores
    return smote_model, "smote", scores


def _tune_threshold(y_true: pd.Series, probs: np.ndarray) -> Tuple[float, float]:
    """Tune decision threshold with F2 emphasis for default detection recall."""
    best_threshold = 0.35
    best_f2 = -1.0
    for threshold in np.arange(0.20, 0.60, 0.01):
        preds = (probs >= threshold).astype(int)
        tp = ((preds == 1) & (y_true == 1)).sum()
        fp = ((preds == 1) & (y_true == 0)).sum()
        fn = ((preds == 0) & (y_true == 1)).sum()
        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        f2 = (5 * precision * recall) / (4 * precision + recall + 1e-9)
        if f2 > best_f2:
            best_f2 = float(f2)
            best_threshold = float(threshold)
    return best_threshold, best_f2


def _evaluate(y_true: pd.Series, probs: np.ndarray, threshold: float) -> Dict[str, float]:
    """Evaluate model predictions with classification and ranking metrics."""
    preds = (probs >= threshold).astype(int)
    return {
        "auc_roc": round(float(roc_auc_score(y_true, probs)), 4),
        "precision": round(float(precision_score(y_true, preds, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, preds, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, preds, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_true, preds)), 4),
        "threshold": round(float(threshold), 2),
    }


def train_full_pipeline(
    train_df: pd.DataFrame,
    target: str,
    features: List[str],
    config: PipelineConfig,
) -> Dict:
    """Train baselines + XGBoost, tune threshold, compute SHAP, and save artifacts."""
    X_train, X_val, X_test, y_train, y_val, y_test = _split_data(
        train_df,
        target,
        features,
        config,
    )

    baseline_metrics = _fit_baselines(
        X_train,
        y_train,
        X_val,
        y_val,
        config.random_state,
    )
    final_model, strategy, xgb_scores = _fit_xgb_candidates(
        X_train,
        y_train,
        X_val,
        y_val,
        config.random_state,
    )

    val_probs = final_model.predict_proba(X_val.fillna(0))[:, 1]
    threshold, best_f2 = _tune_threshold(y_val, val_probs)

    test_probs = final_model.predict_proba(X_test.fillna(0))[:, 1]
    test_metrics = _evaluate(y_test, test_probs, threshold)
    test_metrics["imbalance_strategy"] = strategy
    test_metrics["val_best_f2"] = round(best_f2, 4)
    test_metrics.update({k: round(v, 4) for k, v in baseline_metrics.items()})
    test_metrics.update({k: round(v, 4) for k, v in xgb_scores.items()})

    shap_sample = X_test.fillna(0).sample(
        min(config.shap_sample_size, len(X_test)),
        random_state=config.random_state,
    )
    explainer = shap.TreeExplainer(final_model)
    shap_values = explainer.shap_values(shap_sample)
    shap_global = pd.Series(np.abs(shap_values).mean(axis=0), index=features).sort_values(
        ascending=False
    )

    model_version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    artifact = {
        "model": final_model,
        "features": features,
        "target": target,
        "threshold": threshold,
        "metrics": test_metrics,
        "shap_global_importance": shap_global.to_dict(),
        "model_version": model_version,
        "strategy": strategy,
        "config": asdict(config),
    }

    model_file = output_dir / f"credit_model_{model_version}.pkl"
    with model_file.open("wb") as handle:
        pickle.dump(artifact, handle)

    metrics_file = output_dir / f"metrics_{model_version}.json"
    with metrics_file.open("w", encoding="utf-8") as handle:
        json.dump(test_metrics, handle, indent=2)

    shap_file = output_dir / f"shap_top_{model_version}.json"
    with shap_file.open("w", encoding="utf-8") as handle:
        json.dump(shap_global.head(25).to_dict(), handle, indent=2)

    return {
        "artifact": artifact,
        "model_file": str(model_file),
        "metrics_file": str(metrics_file),
        "shap_file": str(shap_file),
        "X_test": X_test,
        "y_test": y_test,
    }
