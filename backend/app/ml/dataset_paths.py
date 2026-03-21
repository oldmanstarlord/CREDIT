"""Dataset path utilities for canonical workspace dataset layout."""

from pathlib import Path
import os
from typing import Dict


PROJECT_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = PROJECT_ROOT.parent


def _resolve_from_env(name: str, fallback: Path) -> Path:
    """Resolve path from environment variable with fallback."""
    value = os.getenv(name)
    if value:
        return Path(value).expanduser().resolve()
    return fallback.resolve()


DATASETS_ROOT = _resolve_from_env("DATASETS_ROOT", WORKSPACE_ROOT / "datasets")
RAW_DIR = _resolve_from_env("DATASETS_RAW_DIR", DATASETS_ROOT / "raw")
ARCHIVES_DIR = _resolve_from_env("DATASETS_ARCHIVES_DIR", DATASETS_ROOT / "archives")


DATASET_PATHS: Dict[str, Path] = {
    "mytransaction_csv": _resolve_from_env(
        "MYTRANSACTION_CSV", RAW_DIR / "my-transaction" / "MyTransaction.csv"
    ),
    "paysim_fraud_csv": _resolve_from_env(
        "PAYSIM_FRAUD_CSV",
        RAW_DIR / "paysim-fraud" / "PS_20174392719_1491204439457_log.csv",
    ),
    "gmsc_train_csv": _resolve_from_env(
        "GMSC_TRAIN_CSV", RAW_DIR / "give-me-some-credit" / "cs-training.csv"
    ),
    "gmsc_test_csv": _resolve_from_env(
        "GMSC_TEST_CSV", RAW_DIR / "give-me-some-credit" / "cs-test.csv"
    ),
    "gmsc_sample_submission_csv": _resolve_from_env(
        "GMSC_SAMPLE_SUBMISSION_CSV",
        RAW_DIR / "give-me-some-credit" / "sampleEntry.csv",
    ),
    "home_credit_train_csv": _resolve_from_env(
        "HOME_CREDIT_TRAIN_CSV", RAW_DIR / "home-credit" / "application_train.csv"
    ),
    "home_credit_test_csv": _resolve_from_env(
        "HOME_CREDIT_TEST_CSV", RAW_DIR / "home-credit" / "application_test.csv"
    ),
    "home_credit_columns_description_csv": _resolve_from_env(
        "HOME_CREDIT_COLUMNS_DESCRIPTION_CSV",
        RAW_DIR / "home-credit" / "HomeCredit_columns_description.csv",
    ),
    "lending_club_loan_csv": _resolve_from_env(
        "LENDING_CLUB_LOAN_CSV", RAW_DIR / "lending-club" / "loan.csv"
    ),
    "lending_club_dictionary_xlsx": _resolve_from_env(
        "LENDING_CLUB_DICTIONARY_XLSX",
        RAW_DIR / "lending-club" / "LCDataDictionary.xlsx",
    ),
}


def get_dataset_path(name: str) -> Path:
    """Get canonical path for a named dataset key."""
    if name not in DATASET_PATHS:
        valid = ", ".join(sorted(DATASET_PATHS.keys()))
        raise KeyError(f"Unknown dataset key '{name}'. Valid keys: {valid}")
    return DATASET_PATHS[name]


def validate_dataset_layout() -> Dict[str, bool]:
    """Check whether required dataset files currently exist."""
    return {name: path.exists() for name, path in DATASET_PATHS.items()}
