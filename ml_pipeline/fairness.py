"""Fairness monitoring utilities for post-training audits."""

from typing import Dict

import pandas as pd


def run_fairness_audit(
    model,
    X_test: pd.DataFrame,
    sensitive_df: pd.DataFrame,
    threshold: float,
) -> Dict[str, Dict[str, float]]:
    """Compute approval-rate parity and four-fifths rule indicators by group."""
    results: Dict[str, Dict[str, float]] = {}
    group_columns = ["CODE_GENDER", "NAME_EDUCATION_TYPE", "NAME_INCOME_TYPE"]

    for group_col in group_columns:
        if group_col not in sensitive_df.columns:
            continue
        for group_val in sensitive_df[group_col].dropna().unique():
            mask = sensitive_df[group_col] == group_val
            if mask.sum() == 0:
                continue
            probs = model.predict_proba(X_test.loc[mask].fillna(0))[:, 1]
            approval_rate = float((probs < threshold).mean())
            key = f"{group_col}={group_val}"
            results[key] = {"approval_rate": approval_rate, "n": int(mask.sum())}

    if not results:
        return {}

    max_rate = max(v["approval_rate"] for v in results.values())
    for metrics in results.values():
        ratio = metrics["approval_rate"] / max_rate if max_rate else 0.0
        metrics["disparate_impact_ratio"] = round(ratio, 4)
        metrics["bias_flag"] = ratio < 0.80
    return results
