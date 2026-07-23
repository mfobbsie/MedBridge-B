"""
Unit tests for extraction_service.py

Run: pytest tests/unit/test_extraction.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from app.services.extraction_service import (
    extract_text,
    _clean_text,
)
from app.services.document_service import (
    detect_mime_type,
    validate_upload,
    _safe_storage_filename,
)


# ── MIME detection ────────────────────────────────────────────────────────────

def test_detect_pdf_by_magic_bytes():
    assert detect_mime_type(b"%PDF-1.4 rest of file", "doc.pdf") == "application/pdf"


def test_detect_png_by_magic_bytes():
    assert detect_mime_type(b"\x89PNG\r\n\x1a\n", "img.png") == "image/png"


def test_detect_jpeg_by_magic_bytes():
    assert detect_mime_type(b"\xff\xd8\xff\xe0", "img.jpg") == "image/jpeg"


def test_detect_txt_by_extension():
    assert detect_mime_type(b"hello world", "notes.txt") == "text/plain"


def test_unknown_type_returns_none():
    assert detect_mime_type(b"\x00\x00\x00\x00", "file.exe") is None


# ── Validation ────────────────────────────────────────────────────────────────

def test_empty_file_rejected():
    is_valid, error, _ = validate_upload(b"", "doc.pdf")
    assert not is_valid
    assert "empty" in error.lower()


def test_unsupported_type_rejected():
    is_valid, error, _ = validate_upload(b"\x00\x00\x00\x00", "virus.exe")
    assert not is_valid
    assert "Unsupported" in error


def test_oversized_file_rejected():
    big_file = b"%PDF" + b"x" * (11 * 1024 * 1024)  # 11MB
    is_valid, error, _ = validate_upload(big_file, "big.pdf")
    assert not is_valid
    assert "exceeds" in error.lower() or "limit" in error.lower()


def test_valid_pdf_passes():
    pdf_bytes = b"%PDF-1.4 " + b"x" * 1000
    is_valid, error, mime = validate_upload(pdf_bytes, "test.pdf")
    assert is_valid
    assert mime == "application/pdf"


def test_valid_txt_passes():
    is_valid, error, mime = validate_upload(b"Patient LDL 120 mg/dL\n", "lab_result.txt")
    assert is_valid
    assert mime == "text/plain"


# ── Safe storage filename ─────────────────────────────────────────────────────

def test_safe_storage_filename_empty_defaults_to_txt():
    assert _safe_storage_filename("", "text/plain") == "upload.txt"


def test_safe_storage_filename_strips_windows_path():
    assert _safe_storage_filename(r"C:\Users\me\notes.txt", "text/plain") == "notes.txt"


def test_safe_storage_filename_adds_extension_when_missing():
    assert _safe_storage_filename("notes", "text/plain") == "notes.txt"


def test_safe_storage_filename_sanitizes_special_chars():
    assert (
        _safe_storage_filename("## 1. Primary Care Visit Report.txt", "text/plain")
        == "1_Primary_Care_Visit_Report.txt"
    )


# ── Text cleaning ─────────────────────────────────────────────────────────────

def test_clean_text_removes_excess_blanks():
    raw = "Line one\n\n\n\nLine two\n\n\n\nLine three"
    result = _clean_text(raw)
    assert "\n\n\n" not in result
    assert "Line one" in result
    assert "Line three" in result


def test_clean_text_strips_leading_trailing():
    raw = "   \n\nHello\n\n   "
    assert _clean_text(raw) == "Hello"


# ── Plain text extraction ─────────────────────────────────────────────────────

def test_plain_text_extraction():
    content = "Patient Name: John Doe\nDiagnosis: Hypertension\nDate: 2026-01-01"
    result = extract_text(content.encode("utf-8"), "text/plain")
    assert result.success
    assert result.method == "text"
    assert "John Doe" in result.text


def test_plain_text_latin1():
    content = "Café résumé".encode("latin-1")
    result = extract_text(content, "text/plain")
    assert result.success


def test_unsupported_mime_fails_gracefully():
    result = extract_text(b"\x00\x00", "application/octet-stream")
    assert not result.success
    assert result.error_message is not None


# ── OCR ───────────────────────────────────────────────────────────────────────

def test_ocr_low_confidence_sets_flag():
    """OCR below threshold should set low_confidence=True and add a warning."""
    from app.services.extraction_service import ExtractionResult
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    long_text = (
        "Patient Name John Doe Diagnosis Hypertension Treatment Plan Notes "
        "Follow up in two weeks with primary care provider"
    )
    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[0, 0], [10, 0], [10, 10], [0, 10]], long_text, 0.35),
    ]

    with patch(
        "app.services.extraction_service._extract_ocr_via_vision",
        return_value=ExtractionResult(
            text="", method="ocr-vision", confidence=None, success=False,
            error_message="AI unavailable for test",
        ),
    ), patch(
        "app.services.extraction_service._get_easyocr_reader",
        return_value=mock_reader,
    ):
        result = extract_text(jpeg_bytes, "image/jpeg")
        assert result.success
        assert result.method == "ocr-easyocr"
        assert result.low_confidence
        assert result.confidence is not None
        assert any("low" in w.lower() for w in result.warnings)


def test_vision_preferred_for_images():
    """Groq vision is tried first and can succeed without EasyOCR."""
    from app.services.extraction_service import ExtractionResult
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    vision_text = (
        "Patient: Jane Doe\n"
        "Rx: Lisinopril 10mg once daily\n"
        "Prescriber: Dr. Smith\n"
        "Pharmacy fill date: 2026-07-22"
    )
    with patch(
        "app.services.extraction_service._extract_ocr_via_vision",
        return_value=ExtractionResult(
            text=vision_text,
            method="ocr-vision",
            confidence=None,
            success=True,
        ),
    ) as vision_mock, patch(
        "app.services.extraction_service._extract_ocr_via_easyocr"
    ) as easy_mock:
        result = extract_text(jpeg_bytes, "image/jpeg")
        assert result.success
        assert result.method == "ocr-vision"
        assert "Lisinopril" in result.text
        vision_mock.assert_called_once()
        easy_mock.assert_not_called()


def test_easyocr_used_when_vision_fails():
    """When Groq vision fails, EasyOCR can still succeed."""
    from app.services.extraction_service import ExtractionResult
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    ocr_text = (
        "Patient: Jane Doe\n"
        "Rx: Lisinopril 10mg once daily\n"
        "Prescriber: Dr. Smith\n"
        "Pharmacy fill date: 2026-07-22"
    )
    with patch(
        "app.services.extraction_service._extract_ocr_via_vision",
        return_value=ExtractionResult(
            text="", method="ocr-vision", confidence=None, success=False,
            error_message="Vision OCR failed",
        ),
    ), patch(
        "app.services.extraction_service._extract_ocr_via_easyocr",
        return_value=ExtractionResult(
            text=ocr_text,
            method="ocr-easyocr",
            confidence=88.0,
            success=True,
        ),
    ) as easy_mock:
        result = extract_text(jpeg_bytes, "image/jpeg")
        assert result.success
        assert result.method == "ocr-easyocr"
        assert "Lisinopril" in result.text
        easy_mock.assert_called_once()


def test_ocr_prefers_actionable_config_error():
    """When all OCR stages fail, prefer vision/config errors over generic ones."""
    from app.services.extraction_service import ExtractionResult, _extract_ocr
    from PIL import Image
    import io

    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    actionable = (
        "The configured vision model (bad-model) is unavailable "
        "on this Groq account. Set GROQ_VISION_MODEL to a vision-capable model "
        "you have access to, then restart the server."
    )
    with patch(
        "app.services.extraction_service._extract_ocr_via_easyocr",
        return_value=ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=None,
            success=False,
            error_message=(
                "Text could not be extracted from this image. "
                "Please try uploading a clearer photo or a PDF version."
            ),
        ),
    ), patch(
        "app.services.extraction_service._extract_ocr_via_vision",
        return_value=ExtractionResult(
            text="",
            method="ocr-vision",
            confidence=None,
            success=False,
            error_message=actionable,
        ),
    ):
        result = _extract_ocr(jpeg_bytes, "image/jpeg")
        assert not result.success
        assert result.error_message == actionable


def test_easyocr_applies_preprocess_image():
    """EasyOCR path should preprocess the image before readtext."""
    from app.services.extraction_service import ExtractionResult
    from PIL import Image
    import io
    import numpy as np

    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    mock_reader = MagicMock()
    mock_reader.readtext.return_value = [
        ([[0, 0], [10, 0], [10, 10], [0, 10]], "Patient Name John Doe Diagnosis Hypertension Treatment Plan Notes", 0.95),
    ]

    with patch(
        "app.services.extraction_service._extract_ocr_via_vision",
        return_value=ExtractionResult(
            text="", method="ocr-vision", confidence=None, success=False,
            error_message="Vision skipped for EasyOCR preprocess test",
        ),
    ), patch(
        "app.services.extraction_service._get_easyocr_reader",
        return_value=mock_reader,
    ), patch(
        "app.services.extraction_service._preprocess_image",
        wraps=__import__(
            "app.services.extraction_service", fromlist=["_preprocess_image"]
        )._preprocess_image,
    ) as preprocess_mock:
        result = extract_text(jpeg_bytes, "image/jpeg")
        preprocess_mock.assert_called_once()
        assert result.success
        assert result.method == "ocr-easyocr"
        mock_reader.readtext.assert_called_once()
        called_arr = mock_reader.readtext.call_args[0][0]
        assert isinstance(called_arr, np.ndarray)


def test_corrupt_image_fails_gracefully():
    result = extract_text(b"\xff\xd8\xff\x00garbage", "image/jpeg")
    assert not result.success
    assert result.error_message is not None
