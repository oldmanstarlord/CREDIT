"""Dataset loaders and cleaners for GMSC, Home Credit, and transaction data."""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .config import PipelineConfig


def _raw_path(config: PipelineConfig, *parts: str) -> Path:
    """Build absolute path under canonical raw data root."""
    return config.raw_data_root.joinpath(*parts)


def load_mytransaction(config: PipelineConfig, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load and minimally clean MyTransaction.csv with BOM-safe decoding."""
    path = _raw_path(config, "my-transaction", "MyTransaction.csv")
    df = pd.read_csv(path, encoding="utf-8-sig", nrows=nrows)
    df = df.dropna(subset=["Date"])
    df = df[df["Date"].astype(str).str.strip() != ""]
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["Date"])
    df["Month"] = df["Date"].dt.to_period("M")
    df["Withdrawal"] = pd.to_numeric(df["Withdrawal"], errors="coerce").fillna(0.0)
    df["Deposit"] = pd.to_numeric(df["Deposit"], errors="coerce").fillna(0.0)
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce").ffill().fillna(0.0)
    return df


def clean_gmsc(df: pd.DataFrame) -> pd.DataFrame:
    """Apply auditable cleaning rules for Give Me Some Credit data."""
    frame = df.copy()
    if "Unnamed: 0" in frame.columns:
        frame = frame.drop(columns=["Unnamed: 0"])

    frame = frame[frame["age"] >= 18].copy()
    frame["RevolvingUtilizationOfUnsecuredLines"] = frame[
        "RevolvingUtilizationOfUnsecuredLines"
    ].clip(0, 1.5)

    debt_ratio_cap = frame["DebtRatio"].quantile(0.99)
    frame["DebtRatio"] = frame["DebtRatio"].clip(0, debt_ratio_cap)

    past_due_cols = [
        "NumberOfTime30-59DaysPastDueNotWorse",
        "NumberOfTimes90DaysLate",
        "NumberOfTime60-89DaysPastDueNotWorse",
    ]
    for col in past_due_cols:
        frame[col] = frame[col].replace({96: np.nan, 98: np.nan})
        frame[col] = frame[col].fillna(0).astype(int)

    frame["age_group"] = pd.cut(
        frame["age"],
        bins=[18, 30, 40, 50, 60, 70, 120],
        labels=["18-30", "30-40", "40-50", "50-60", "60-70", "70+"],
        include_lowest=True,
    )
    income_medians = frame.groupby("age_group", observed=False)["MonthlyIncome"].median()
    income_missing = frame["MonthlyIncome"].isna()

    def _impute_income(row: pd.Series) -> float:
        if pd.notna(row["MonthlyIncome"]):
            return float(row["MonthlyIncome"])
        group_median = income_medians.get(row["age_group"], np.nan)
        if pd.notna(group_median):
            return float(group_median)
        return float(frame["MonthlyIncome"].median())

    frame["MonthlyIncome"] = frame.apply(_impute_income, axis=1)
    frame["MonthlyIncome_was_imputed"] = income_missing.astype(int)

    frame["NumberOfDependents"] = frame["NumberOfDependents"].fillna(0).astype(int)
    return frame


def load_gmsc_train(config: PipelineConfig, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load and clean Give Me Some Credit training set."""
    path = _raw_path(config, "give-me-some-credit", "cs-training.csv")
    return clean_gmsc(pd.read_csv(path, nrows=nrows))


def load_gmsc_test(config: PipelineConfig, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load and clean Give Me Some Credit test set."""
    path = _raw_path(config, "give-me-some-credit", "cs-test.csv")
    return clean_gmsc(pd.read_csv(path, nrows=nrows))


def clean_home_credit_application(df: pd.DataFrame) -> pd.DataFrame:
    """Apply baseline cleaning and transformations for Home Credit application data."""
    frame = df.copy()

    frame["age_years"] = (-frame["DAYS_BIRTH"] / 365).round(1)
    frame["employment_years"] = np.where(
        frame["DAYS_EMPLOYED"] == 365243,
        0,
        (-frame["DAYS_EMPLOYED"] / 365).clip(0, 50),
    )
    frame["is_employed"] = (frame["DAYS_EMPLOYED"] != 365243).astype(int)

    for col in ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]:
        frame[f"has_{col.lower()}"] = (~frame[col].isna()).astype(int)
        frame[col] = frame[col].fillna(frame[col].median())
    frame["ext_source_count"] = (
        frame["has_ext_source_1"] + frame["has_ext_source_2"] + frame["has_ext_source_3"]
    )

    doc_cols = [c for c in frame.columns if c.startswith("FLAG_DOCUMENT_")]
    if doc_cols:
        frame["total_documents_provided"] = frame[doc_cols].sum(axis=1)
    else:
        frame["total_documents_provided"] = 0

    building_cols = [
        c for c in frame.columns if c.endswith("_AVG") or c.endswith("_MODE") or c.endswith("_MEDI")
    ]
    # Some *_MODE fields are categorical strings (for example, housing fund account type).
    # Coerce only numeric columns with median and use mode fallback for categorical columns.
    for col in building_cols:
        if pd.api.types.is_numeric_dtype(frame[col]):
            frame[col] = frame[col].fillna(frame[col].median())
        else:
            mode_vals = frame[col].mode(dropna=True)
            fill_val = mode_vals.iloc[0] if not mode_vals.empty else "UNKNOWN"
            frame[col] = frame[col].fillna(fill_val)

    return frame


def load_home_credit_train(config: PipelineConfig, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load and clean Home Credit application_train.csv."""
    path = _raw_path(config, "home-credit", "application_train.csv")
    return clean_home_credit_application(pd.read_csv(path, nrows=nrows))


def load_home_credit_test(config: PipelineConfig, nrows: Optional[int] = None) -> pd.DataFrame:
    """Load and clean Home Credit application_test.csv."""
    path = _raw_path(config, "home-credit", "application_test.csv")
    return clean_home_credit_application(pd.read_csv(path, nrows=nrows))


def load_installments(config: PipelineConfig) -> Optional[pd.DataFrame]:
    """Load installments_payments if available."""
    path = _raw_path(config, "home-credit", "installments_payments.csv")
    if not path.exists():
        return None
    return pd.read_csv(path)


def load_previous_applications(config: PipelineConfig) -> Optional[pd.DataFrame]:
    """Load previous_application if available."""
    path = _raw_path(config, "home-credit", "previous_application.csv")
    if not path.exists():
        return None
    return pd.read_csv(path)
