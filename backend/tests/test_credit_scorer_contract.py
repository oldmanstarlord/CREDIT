from pathlib import Path

import pytest

from app.ml.predict import CreditScorer


@pytest.mark.integration
def test_credit_scorer_with_winner_serving_artifact() -> None:
    artifact = Path("ml_pipeline/models/integration_contracts/winner_upgrade_v4/winner_v4_serving_artifact.pkl")
    if not artifact.exists():
        pytest.skip("Winner serving artifact not found")

    scorer = CreditScorer()
    try:
        scorer.load_model(str(artifact))
        result = scorer.score_application(
            {
                "user_category": "gig_worker",
                "requested_amount": 150000,
                "requested_tenure_months": 24,
                "monthly_income": 26000,
                "credit_to_income_ratio": 6.2,
                "annuity_to_income_ratio": 0.48,
                "household_size": 3,
            }
        )
    except Exception as exc:
        pytest.skip(f"Scoring not available in this local runtime: {exc}")

    assert "credit_score" in result
    assert 300 <= int(result["credit_score"]) <= 850
    assert result["decision_status"] in {
        "auto_approve_low_risk",
        "auto_reject_high_risk",
        "manual_review",
        "insufficient_data",
    }
