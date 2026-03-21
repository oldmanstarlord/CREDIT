from pathlib import Path

from app.api.routes.applications import _resolve_winner_contract_model


def test_resolve_winner_contract_model_points_to_serving_artifact() -> None:
    model_path = Path(_resolve_winner_contract_model())
    assert model_path.exists()
    assert model_path.name == "winner_v4_serving_artifact.pkl"
