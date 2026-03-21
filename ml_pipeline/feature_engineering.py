"""Feature engineering for GMSC, Home Credit, and transaction-based alternative data."""

from typing import Dict

import numpy as np
import pandas as pd


def engineer_gmsc_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create financially meaningful derived features for GMSC."""
    frame = df.copy()

    frame["total_past_due_events"] = (
        frame["NumberOfTime30-59DaysPastDueNotWorse"]
        + frame["NumberOfTime60-89DaysPastDueNotWorse"]
        + frame["NumberOfTimes90DaysLate"]
    )
    frame["weighted_delinquency_score"] = (
        frame["NumberOfTime30-59DaysPastDueNotWorse"] * 1
        + frame["NumberOfTime60-89DaysPastDueNotWorse"] * 2
        + frame["NumberOfTimes90DaysLate"] * 4
    )
    frame["income_per_dependent"] = frame["MonthlyIncome"] / (frame["NumberOfDependents"] + 1)
    frame["estimated_monthly_debt"] = frame["DebtRatio"] * frame["MonthlyIncome"]
    frame["debt_service_ratio"] = frame["estimated_monthly_debt"] / (frame["MonthlyIncome"] + 1)
    frame["is_over_utilized"] = (frame["RevolvingUtilizationOfUnsecuredLines"] > 0.7).astype(int)
    frame["is_maxed_out"] = (frame["RevolvingUtilizationOfUnsecuredLines"] > 0.95).astype(int)
    frame["age_income_ratio"] = frame["age"] / (frame["MonthlyIncome"] / 1000 + 1)
    frame["has_90day_default"] = (frame["NumberOfTimes90DaysLate"] > 0).astype(int)
    frame["has_any_delinquency"] = (frame["total_past_due_events"] > 0).astype(int)
    frame["credit_diversity"] = frame["NumberOfOpenCreditLinesAndLoans"] / (
        frame["NumberRealEstateLoansOrLines"] + 1
    )
    frame["log_monthly_income"] = np.log1p(frame["MonthlyIncome"])
    frame["log_revolving_util"] = np.log1p(frame["RevolvingUtilizationOfUnsecuredLines"])
    return frame


def engineer_home_credit_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create high-value derived ratios and alternative signals for Home Credit."""
    frame = df.copy()

    frame["AMT_ANNUITY"] = frame["AMT_ANNUITY"].fillna(frame["AMT_ANNUITY"].median())
    frame["AMT_GOODS_PRICE"] = frame["AMT_GOODS_PRICE"].fillna(frame["AMT_GOODS_PRICE"].median())
    frame["CNT_FAM_MEMBERS"] = frame["CNT_FAM_MEMBERS"].fillna(frame["CNT_FAM_MEMBERS"].median())

    frame["credit_to_income_ratio"] = frame["AMT_CREDIT"] / (frame["AMT_INCOME_TOTAL"] + 1)
    frame["annuity_to_income_ratio"] = frame["AMT_ANNUITY"] / (frame["AMT_INCOME_TOTAL"] / 12 + 1)
    frame["credit_to_goods_ratio"] = frame["AMT_CREDIT"] / (frame["AMT_GOODS_PRICE"] + 1)
    frame["income_per_family_member"] = frame["AMT_INCOME_TOTAL"] / (frame["CNT_FAM_MEMBERS"] + 1)

    ext_cols = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
    frame["ext_source_mean"] = frame[ext_cols].mean(axis=1)
    frame["ext_source_min"] = frame[ext_cols].min(axis=1)
    frame["ext_source_product"] = frame["EXT_SOURCE_1"] * frame["EXT_SOURCE_2"] * frame["EXT_SOURCE_3"]

    frame["social_circle_default_rate_30"] = frame["DEF_30_CNT_SOCIAL_CIRCLE"].fillna(0) / (
        frame["OBS_30_CNT_SOCIAL_CIRCLE"].fillna(0) + 1
    )
    frame["social_circle_default_rate_60"] = frame["DEF_60_CNT_SOCIAL_CIRCLE"].fillna(0) / (
        frame["OBS_60_CNT_SOCIAL_CIRCLE"].fillna(0) + 1
    )
    frame["social_risk_composite"] = (
        frame["social_circle_default_rate_30"] + frame["social_circle_default_rate_60"]
    ) / 2

    mismatch_cols = [
        "REG_REGION_NOT_LIVE_REGION",
        "REG_CITY_NOT_LIVE_CITY",
        "REG_CITY_NOT_WORK_CITY",
        "LIVE_CITY_NOT_WORK_CITY",
    ]
    existing_mismatch_cols = [c for c in mismatch_cols if c in frame.columns]
    frame["address_instability_score"] = frame[existing_mismatch_cols].fillna(0).sum(axis=1)

    frame["enquiry_last_month"] = frame["AMT_REQ_CREDIT_BUREAU_MON"].fillna(0)
    frame["enquiry_last_year"] = frame["AMT_REQ_CREDIT_BUREAU_YEAR"].fillna(0)
    frame["enquiry_acceleration"] = frame["enquiry_last_month"] / (
        frame["enquiry_last_year"] / 12 + 1
    )

    contact_flags = ["FLAG_MOBIL", "FLAG_EMP_PHONE", "FLAG_CONT_MOBILE", "FLAG_EMAIL"]
    frame["contact_score"] = frame[contact_flags].fillna(0).sum(axis=1) / len(contact_flags)

    frame["employment_to_age_ratio"] = frame["employment_years"] / (frame["age_years"] + 1)

    frame["days_since_phone_change"] = (-frame["DAYS_LAST_PHONE_CHANGE"]).clip(0, 3650)
    frame["recently_changed_phone"] = (frame["days_since_phone_change"] < 30).astype(int)

    frame["REGION_RATING_CLIENT"] = frame["REGION_RATING_CLIENT"].fillna(
        frame["REGION_RATING_CLIENT"].median()
    )
    return frame


def aggregate_installments(installments_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate payment behavior features from installments table."""
    frame = installments_df.copy()
    frame["payment_lateness"] = frame["DAYS_ENTRY_PAYMENT"] - frame["DAYS_INSTALMENT"]
    frame["payment_ratio"] = frame["AMT_PAYMENT"] / (frame["AMT_INSTALMENT"] + 1)

    agg = frame.groupby("SK_ID_CURR").agg(
        installment_count=("AMT_PAYMENT", "count"),
        total_paid=("AMT_PAYMENT", "sum"),
        avg_payment_ratio=("payment_ratio", "mean"),
        min_payment_ratio=("payment_ratio", "min"),
        late_payment_count=("payment_lateness", lambda x: (x > 0).sum()),
        avg_days_late=("payment_lateness", lambda x: x[x > 0].mean()),
        early_payment_count=("payment_lateness", lambda x: (x < 0).sum()),
        max_days_late=("payment_lateness", "max"),
    )
    agg = agg.reset_index()
    agg["late_payment_rate"] = agg["late_payment_count"] / (agg["installment_count"] + 1)
    agg["early_payment_rate"] = agg["early_payment_count"] / (agg["installment_count"] + 1)
    agg = agg.fillna(0)
    return agg


def aggregate_previous_applications(prev_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate historical previous application behavior per applicant."""
    agg = prev_df.groupby("SK_ID_CURR").agg(
        prev_app_count=("SK_ID_PREV", "count"),
        prev_approved_count=("NAME_CONTRACT_STATUS", lambda x: (x == "Approved").sum()),
        prev_refused_count=("NAME_CONTRACT_STATUS", lambda x: (x == "Refused").sum()),
        prev_cancelled_count=("NAME_CONTRACT_STATUS", lambda x: (x == "Canceled").sum()),
        avg_prev_credit=("AMT_CREDIT", "mean"),
        max_prev_credit=("AMT_CREDIT", "max"),
        avg_prev_annuity=("AMT_ANNUITY", "mean"),
    )
    agg = agg.reset_index()
    agg["approval_rate"] = agg["prev_approved_count"] / (agg["prev_app_count"] + 1)
    agg["refusal_rate"] = agg["prev_refused_count"] / (agg["prev_app_count"] + 1)
    agg["credit_growth"] = agg["max_prev_credit"] / (agg["avg_prev_credit"] + 1)
    agg = agg.fillna(0)
    return agg


def extract_transaction_features(df: pd.DataFrame) -> Dict[str, float]:
    """Extract alternative behavioral credit signals from transaction history."""
    monthly_deposits = df.groupby("Month")["Deposit"].sum()
    monthly_count = df.groupby("Month").size()

    def _safe_cv(series: pd.Series) -> float:
        return float(series.std() / (series.mean() + 1e-9))

    def _bounded(value: float, lower: float, upper: float) -> float:
        return float(max(lower, min(upper, value)))

    income_stability = _bounded(1 - _safe_cv(monthly_deposits), 0.0, 1.0)

    salary_events = df[df["Category"] == "Salary"]
    if len(salary_events) < 2:
        salary_regularity = 0.0
    else:
        salary_regularity = _bounded(1 - _safe_cv(salary_events["Deposit"]), 0.0, 1.0)

    monthly = df.groupby("Month").agg(
        deposits=("Deposit", "sum"),
        withdrawals=("Withdrawal", "sum"),
    )
    cash_flow = monthly["deposits"] - monthly["withdrawals"]
    cash_flow_volatility = _bounded(_safe_cv(cash_flow.abs() + 1), 0.0, 10.0)

    avg_balance = float(df["Balance"].mean())
    stress_threshold = avg_balance * 0.05
    balance_stress_indicator = float((df["Balance"] < stress_threshold).mean())

    rent_payments = df[df["Category"] == "Rent"]["Withdrawal"]
    monthly_rent = float(rent_payments.mean()) if len(rent_payments) else 0.0
    if monthly_rent > 0:
        savings_buffer_ratio = _bounded((avg_balance / monthly_rent) / 5.0, 0.0, 1.0)
    else:
        savings_buffer_ratio = _bounded(avg_balance / 10000.0, 0.0, 1.0)

    essential_spend = df[df["Category"].isin(["Food", "Rent", "Transport"])]["Withdrawal"].sum()
    total_spend = df["Withdrawal"].sum()
    spending_pattern_ratio = float(essential_spend / (total_spend + 1e-9))

    transaction_consistency = _bounded(1 - _safe_cv(monthly_count), 0.0, 1.0)
    misc = df[df["Category"] == "Misc"]
    small_recurring = misc[(misc["Withdrawal"] >= 50) & (misc["Withdrawal"] <= 500)]
    utility_payment_proxy = _bounded(len(small_recurring) / max(len(misc), 1) * 2, 0.0, 1.0)

    return {
        "income_stability": income_stability,
        "salary_regularity": salary_regularity,
        "cash_flow_volatility": cash_flow_volatility,
        "balance_stress_indicator": balance_stress_indicator,
        "savings_buffer_ratio": savings_buffer_ratio,
        "spending_pattern_ratio": spending_pattern_ratio,
        "transaction_consistency": transaction_consistency,
        "utility_payment_proxy": utility_payment_proxy,
        "avg_monthly_income": float(monthly_deposits.mean()),
        "avg_monthly_expense": float(df.groupby("Month")["Withdrawal"].sum().mean()),
        "avg_running_balance": avg_balance,
        "min_balance_ever": float(df["Balance"].min()),
        "total_salary_events": int((df["Category"] == "Salary").sum()),
        "food_spend_ratio": float(
            df[df["Category"] == "Food"]["Withdrawal"].sum() / (total_spend + 1e-9)
        ),
        "avg_txns_per_month": float(monthly_count.mean()),
    }
