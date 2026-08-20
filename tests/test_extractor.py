from unittest.mock import MagicMock, patch

from google.genai import errors

from src.importer.extractor import extract_recipe_from_image
from src.importer.schema import ExtractedRecipe, ExtractedIngredient


def _make_api_error(code: int) -> errors.APIError:
    return errors.APIError(code=code, response_json={"error": {"message": "boom"}})


SAMPLE_EXTRACTED = ExtractedRecipe(
    name="Grandma's Cookies",
    ingredients=[ExtractedIngredient(quantity=2, unit="cup", name="flour")],
    instructions=["Mix.", "Bake at 350F for 12 min."],
    extraction_confidence="medium",
    extraction_notes="Quantity for vanilla was illegible, assumed 1 tsp.",
)


def test_rejects_empty_image_bytes():
    result = extract_recipe_from_image(b"", "image/png")

    assert result["success"] is False
    assert "No image data" in result["error"]


def test_rejects_unsupported_mime_type():
    result = extract_recipe_from_image(b"fakebytes", "image/gif")

    assert result["success"] is False
    assert "Unsupported image type" in result["error"]


@patch.dict("os.environ", {}, clear=True)
def test_missing_api_key_returns_error():
    result = extract_recipe_from_image(b"fakebytes", "image/png")

    assert result["success"] is False
    assert "GOOGLE_API_KEY" in result["error"]


@patch("src.importer.extractor.genai.Client")
@patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"})
def test_successful_extraction_returns_recipe_dict(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(parsed=SAMPLE_EXTRACTED)
    mock_client_cls.return_value = mock_client

    result = extract_recipe_from_image(b"fakebytes", "image/png")

    assert result["success"] is True
    assert result["recipe"]["name"] == "Grandma's Cookies"
    assert result["recipe"]["extraction_confidence"] == "medium"
    assert len(result["recipe"]["ingredients"]) == 1


@patch("src.importer.extractor.genai.Client")
@patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"})
def test_none_parsed_response_returns_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(parsed=None)
    mock_client_cls.return_value = mock_client

    result = extract_recipe_from_image(b"fakebytes", "image/png")

    assert result["success"] is False
    assert "expected recipe structure" in result["error"]


@patch("src.importer.extractor.time.sleep")
@patch("src.importer.extractor.genai.Client")
@patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"})
def test_retries_on_transient_error_then_succeeds(mock_client_cls, mock_sleep):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = [
        _make_api_error(503),
        MagicMock(parsed=SAMPLE_EXTRACTED),
    ]
    mock_client_cls.return_value = mock_client

    result = extract_recipe_from_image(b"fakebytes", "image/png")

    assert result["success"] is True
    assert mock_client.models.generate_content.call_count == 2


@patch("src.importer.extractor.genai.Client")
@patch.dict("os.environ", {"GOOGLE_API_KEY": "fake-key"})
def test_non_retryable_error_fails_immediately(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = _make_api_error(400)
    mock_client_cls.return_value = mock_client

    result = extract_recipe_from_image(b"fakebytes", "image/png")

    assert result["success"] is False
    assert mock_client.models.generate_content.call_count == 1