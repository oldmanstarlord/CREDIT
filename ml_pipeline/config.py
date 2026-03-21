"""Configuration for the standalone ML pipeline."""

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for model training and evaluation."""

    random_state: int = 42
    test_size: float = 0.20
    val_size: float = 0.10
    cv_folds: int = 5
    decision_threshold_start: float = 0.35
    shap_sample_size: int = 1000
    model_output_dir: str = "ml_pipeline/models"
    optimize_hyperparams: bool = False
    optuna_trials: int = 30

    @property
    def project_root(self) -> Path:
        """Resolve absolute project root path."""
        return Path(__file__).resolve().parents[1]

    @property
    def workspace_root(self) -> Path:
        """Resolve absolute workspace root path."""
        return self.project_root.parent

    @property
    def datasets_root(self) -> Path:
        """Resolve canonical dataset root path."""
        return self.workspace_root / "datasets"

    @property
    def raw_data_root(self) -> Path:
        """Resolve canonical raw datasets path."""
        return self.datasets_root / "raw"

    @property
    def output_dir(self) -> Path:
        """Resolve output artifact directory path."""
        return self.project_root / self.model_output_dir


GMSC_BASE_FEATURES: List[str] = [
    "RevolvingUtilizationOfUnsecuredLines",
    "age",
    "NumberOfTime30-59DaysPastDueNotWorse",
    "DebtRatio",
    "MonthlyIncome",
    "NumberOfOpenCreditLinesAndLoans",
    "NumberOfTimes90DaysLate",
    "NumberRealEstateLoansOrLines",
    "NumberOfTime60-89DaysPastDueNotWorse",
    "NumberOfDependents",
]

GMSC_ENGINEERED_FEATURES: List[str] = [
    "total_past_due_events",
    "weighted_delinquency_score",
    "income_per_dependent",
    "estimated_monthly_debt",
    "debt_service_ratio",
    "is_over_utilized",
    "is_maxed_out",
    "age_income_ratio",
    "has_90day_default",
    "has_any_delinquency",
    "credit_diversity",
    "log_monthly_income",
    "log_revolving_util",
    "MonthlyIncome_was_imputed",
]

GMSC_FEATURES: List[str] = GMSC_BASE_FEATURES + GMSC_ENGINEERED_FEATURES

HOME_CREDIT_BASE_FEATURES: List[str] = [
    "age_years",
    "employment_years",
    "is_employed",
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
    "ext_source_count",
    "REGION_RATING_CLIENT",
]

HOME_CREDIT_ENGINEERED_FEATURES: List[str] = [
    "credit_to_income_ratio",
    "annuity_to_income_ratio",
    "credit_to_goods_ratio",
    "income_per_family_member",
    "ext_source_mean",
    "ext_source_min",
    "ext_source_product",
    "social_risk_composite",
    "address_instability_score",
    "enquiry_last_month",
    "enquiry_last_year",
    "enquiry_acceleration",
    "contact_score",
    "employment_to_age_ratio",
    "total_documents_provided",
    "days_since_phone_change",
    "recently_changed_phone",
]

HOME_CREDIT_FEATURES: List[str] = HOME_CREDIT_BASE_FEATURES + HOME_CREDIT_ENGINEERED_FEATURES
