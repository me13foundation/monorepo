import json
from pathlib import Path

from src.infrastructure.validation.api_response_validator import APIResponseValidator

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "api_samples"


def load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open() as handle:
        return json.load(handle)


def test_validate_clinvar_search_sample() -> None:
    data = load_fixture("clinvar_search_response.json")
    result = APIResponseValidator.validate_clinvar_search_response(data)

    assert result["is_valid"] is True
    sanitized = result["sanitized_data"]
    assert sanitized is not None
    assert len(sanitized["esearchresult"]["idlist"]) > 0


def test_validate_clinvar_variant_sample() -> None:
    data = load_fixture("clinvar_variant_response.json")
    result = APIResponseValidator.validate_clinvar_variant_response(data)

    assert result["is_valid"] is True
    sanitized = result["sanitized_data"]
    assert sanitized is not None
    assert "result" in sanitized
    # ClinVar responses include a "uids" collection alongside keyed records
    assert "uids" in sanitized["result"]
