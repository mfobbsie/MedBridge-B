"""
Text extraction service.

Handles three document types:
  - PDF        → pdfplumber (fallback: PyMuPDF)
  - PNG/JPEG   → Groq vision, then EasyOCR (pip)
  - Plain text → direct read

Returns ExtractionResult with text, confidence, and any warnings.
"""

import base64
import io
import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import pdfplumber
import fitz  # PyMuPDF fallback
from groq import Groq
from PIL import Image, ImageFilter, ImageEnhance
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import get_settings

logger = logging.getLogger(__name__)

_easyocr_reader = None
_easyocr_lock = threading.Lock()

VISION_OCR_SYSTEM_PROMPT = """You are MedBridge, a document text extraction tool.

Extract ALL readable text from the document image exactly as it appears.
Preserve line breaks and reading order where possible.
Do not invent text that is not visible.
Do not summarize, explain, or add commentary.
Return only the extracted text."""


@dataclass
class ExtractionResult:
    text: str
    method: str                     # "pdf" | "ocr-easyocr" | "ocr-vision" | "text"
    confidence: Optional[float]     # 0-100 for OCR; None for PDF/text/vision
    low_confidence: bool = False
    warnings: list[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


def extract_text(file_bytes: bytes, mime_type: str) -> ExtractionResult:
    """
    Main entry point. Dispatches to the correct extractor based on MIME type.
    Never raises — always returns an ExtractionResult (success or failure).
    """
    try:
        if mime_type == "application/pdf":
            return _extract_pdf(file_bytes)
        elif mime_type in ("image/png", "image/jpeg", "image/jpg"):
            return _extract_ocr(file_bytes, mime_type)
        elif mime_type in ("text/plain",):
            return _extract_text(file_bytes)
        else:
            return ExtractionResult(
                text="",
                method="unknown",
                confidence=None,
                success=False,
                error_message=f"Unsupported file type: {mime_type}",
            )
    except Exception as e:
        logger.exception(f"Extraction failed unexpectedly: {e}")
        return ExtractionResult(
            text="",
            method="unknown",
            confidence=None,
            success=False,
            error_message="An unexpected error occurred during text extraction.",
        )


# ── PDF ───────────────────────────────────────────────────────────────────────

def _extract_pdf(file_bytes: bytes) -> ExtractionResult:
    """
    Try pdfplumber first. If it returns < 50 chars (scanned PDF),
    fall through to OCR on the first page. If that also fails, try PyMuPDF.
    """
    text = _pdf_pdfplumber(file_bytes)

    if len(text.strip()) >= 50:
        return ExtractionResult(text=_clean_text(text), method="pdf", confidence=None)

    # Looks like a scanned PDF — try OCR on page images
    logger.info("PDF appears scanned or image-based; routing to OCR")
    ocr_result = _pdf_ocr_fallback(file_bytes)
    if ocr_result.success and len(ocr_result.text.strip()) >= 50:
        ocr_result.warnings.append(
            "This document appeared to be a scanned image. "
            "Text was extracted using OCR and may contain minor errors."
        )
        return ocr_result

    # Last resort: PyMuPDF
    logger.info("Attempting PyMuPDF fallback")
    pymupdf_text = _pdf_pymupdf(file_bytes)
    if len(pymupdf_text.strip()) >= 50:
        return ExtractionResult(
            text=_clean_text(pymupdf_text),
            method="pdf-pymupdf",
            confidence=None,
            warnings=["Document required fallback extraction. Some formatting may be lost."],
        )

    return ExtractionResult(
        text="",
        method="pdf",
        confidence=None,
        success=False,
        error_message=(
            "This document could not be processed. "
            "Please upload a clearer image or a text-based PDF version."
        ),
    )


def _pdf_pdfplumber(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _pdf_pymupdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)


def _pdf_ocr_fallback(file_bytes: bytes) -> ExtractionResult:
    """Render first page of scanned PDF as image, then OCR it."""
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page = doc[0]
        mat = fitz.Matrix(2, 2)  # 2x zoom = ~144 DPI
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        return _extract_ocr(img_bytes, "image/png")
    except Exception as e:
        logger.warning(f"PDF OCR fallback failed: {e}")
        return ExtractionResult(
            text="", method="ocr", confidence=None, success=False,
            error_message="Could not render PDF pages for OCR.",
        )


# ── OCR ───────────────────────────────────────────────────────────────────────

def _get_easyocr_reader():
    """Lazy-load a shared EasyOCR reader (models download on first use)."""
    global _easyocr_reader
    if _easyocr_reader is not None:
        return _easyocr_reader
    with _easyocr_lock:
        if _easyocr_reader is not None:
            return _easyocr_reader
        import easyocr

        logger.info("Initializing EasyOCR reader (first run may download models)...")
        _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return _easyocr_reader


def _extract_ocr_via_easyocr(file_bytes: bytes) -> ExtractionResult:
    """Extract text with EasyOCR (pip package)."""
    settings = get_settings()

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img = _preprocess_image(img)
        # EasyOCR expects RGB ndarray (H, W, C).
        if img.mode != "RGB":
            img = img.convert("RGB")
    except Exception:
        return ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=None,
            success=False,
            error_message="Could not open image file. Please ensure it is a valid PNG or JPEG.",
        )

    try:
        import numpy as np

        reader = _get_easyocr_reader()
        results = reader.readtext(np.array(img), detail=1, paragraph=False)
    except ImportError as e:
        logger.warning("EasyOCR dependencies missing: %s", e)
        return ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=None,
            success=False,
            error_message=(
                "EasyOCR is not installed in this environment. "
                "Run: pip install easyocr"
            ),
        )
    except Exception as e:
        logger.exception("EasyOCR failed: %s", e)
        return ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=None,
            success=False,
            error_message=(
                "Text could not be extracted from this image. "
                "Please try uploading a clearer photo or a PDF version."
            ),
        )

    if not results:
        return ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=0.0,
            success=False,
            error_message=(
                "Very little text was found in this image. "
                "Please upload a clearer photo or a PDF version of your document."
            ),
        )

    # results: list of (bbox, text, confidence 0-1)
    lines = [str(item[1]).strip() for item in results if item[1] and str(item[1]).strip()]
    confidences = [float(item[2]) * 100.0 for item in results if len(item) >= 3]
    text = _clean_text("\n".join(lines))
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    low_confidence = mean_confidence < settings.ocr_confidence_threshold
    warnings = []

    if low_confidence:
        warnings.append(
            f"Text extraction confidence was low ({mean_confidence:.0f}%). "
            "Some words may have been misread. "
            "For best results, upload a well-lit, flat photo or a PDF."
        )

    if len(text.strip()) < 50:
        return ExtractionResult(
            text="",
            method="ocr-easyocr",
            confidence=round(mean_confidence, 1),
            success=False,
            error_message=(
                "Very little text was found in this image. "
                "Please upload a clearer photo or a PDF version of your document."
            ),
        )

    return ExtractionResult(
        text=text,
        method="ocr-easyocr",
        confidence=round(mean_confidence, 1),
        low_confidence=low_confidence,
        warnings=warnings,
    )


def _image_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """Encode image for Groq vision; shrink large payloads to stay under size guidance."""
    data = image_bytes
    if len(base64.b64encode(data)) > 3_500_000:
        try:
            img = Image.open(io.BytesIO(data))
            img = img.convert("RGB")
            img.thumbnail((1600, 1600))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            data = buf.getvalue()
            mime_type = "image/jpeg"
        except Exception as e:
            logger.warning("Image shrink failed: %s", e)
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime_type};base64,{b64}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
    retry=lambda rs: not _is_permanent_vision_error(rs.outcome.exception() if rs.outcome else None),
)
def _call_vision_ocr(client: Groq, model: str, messages: list[dict]) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=2000,
        temperature=0.1,
    )
    return (response.choices[0].message.content or "").strip()


def _is_permanent_vision_error(exc: Optional[BaseException]) -> bool:
    if exc is None:
        return False
    err = str(exc).lower()
    return (
        "model_not_found" in err
        or "does not exist" in err
        or "do not have access" in err
        or "model_decommissioned" in err
        or "decommissioned" in err
    )


def _extract_ocr_via_vision(file_bytes: bytes, mime_type: str) -> ExtractionResult:
    """Extract text from an image using Groq vision (no local OCR install required)."""
    settings = get_settings()
    if not settings.groq_api_key:
        return ExtractionResult(
            text="",
            method="ocr-vision",
            confidence=None,
            success=False,
            error_message="AI service is not configured.",
        )

    try:
        Image.open(io.BytesIO(file_bytes))
    except Exception:
        return ExtractionResult(
            text="",
            method="ocr-vision",
            confidence=None,
            success=False,
            error_message="Could not open image file. Please ensure it is a valid PNG or JPEG.",
        )

    client = Groq(api_key=settings.groq_api_key)
    data_url = _image_to_data_url(file_bytes, mime_type)
    messages = [
        {"role": "system", "content": VISION_OCR_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Extract all readable text from this medical document image.",
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]

    try:
        text = _clean_text(_call_vision_ocr(client, settings.groq_vision_model, messages))
    except Exception as e:
        logger.exception("Vision OCR failed: %s", e)
        err = str(e).lower()
        if "model_not_found" in err or "does not exist" in err or "do not have access" in err:
            error_message = (
                f"The configured vision model ({settings.groq_vision_model}) is unavailable "
                "on this Groq account. Set GROQ_VISION_MODEL to a vision-capable model "
                "you have access to, then restart the server."
            )
        elif "model_decommissioned" in err or "decommissioned" in err:
            error_message = (
                f"The configured vision model ({settings.groq_vision_model}) is no longer "
                "supported by Groq. Update GROQ_VISION_MODEL in your .env and restart."
            )
        else:
            error_message = (
                "Text could not be extracted from this image. "
                "Please try uploading a clearer photo or a PDF version."
            )
        return ExtractionResult(
            text="",
            method="ocr-vision",
            confidence=None,
            success=False,
            error_message=error_message,
        )

    if len(text.strip()) < 50:
        return ExtractionResult(
            text="",
            method="ocr-vision",
            confidence=None,
            success=False,
            error_message=(
                "Very little text was found in this image. "
                "Please upload a clearer photo or a PDF version of your document."
            ),
        )

    return ExtractionResult(
        text=text,
        method="ocr-vision",
        confidence=None,
        warnings=["Text was extracted with AI vision OCR and may contain minor errors."],
    )


def _is_actionable_ocr_error(message: Optional[str]) -> bool:
    """True when the message points at config/install issues the user can fix."""
    if not message:
        return False
    lower = message.lower()
    return any(
        token in lower
        for token in (
            "not installed",
            "not configured",
            "not available",
            "unavailable",
            "groq_vision_model",
            "vision model",
            "does not exist",
            "do not have access",
            "decommissioned",
            "no longer supported",
            "pip install",
            "set groq",
            "update groq_vision_model",
        )
    )


def _prefer_ocr_error(
    *results: ExtractionResult,
) -> ExtractionResult:
    """Prefer actionable config/install errors over generic extraction failures."""
    with_message = [r for r in results if r.error_message]
    for result in with_message:
        if _is_actionable_ocr_error(result.error_message):
            return result
    return with_message[0] if with_message else results[0]


def _extract_ocr(file_bytes: bytes, mime_type: str = "image/png") -> ExtractionResult:
    """
    Extract text from an image.

    Order: Groq vision → EasyOCR (pip).
    """
    vision_result = _extract_ocr_via_vision(file_bytes, mime_type)
    if vision_result.success:
        return vision_result
    logger.info(
        "Vision OCR stage failed: %s",
        vision_result.error_message or "no text extracted",
    )

    easyocr_result = _extract_ocr_via_easyocr(file_bytes)
    if easyocr_result.success:
        return easyocr_result
    logger.info(
        "EasyOCR stage failed: %s",
        easyocr_result.error_message or "no text extracted",
    )

    return _prefer_ocr_error(vision_result, easyocr_result)


def _preprocess_image(img: Image.Image) -> Image.Image:
    """Apply preprocessing to improve OCR accuracy on phone photos."""
    # Convert to RGB if needed (handles RGBA, palette modes)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Resize: target 300 DPI equivalent
    # Most phone photos are high-res already; scale up small images
    min_dimension = 1800
    if min(img.size) < min_dimension:
        scale = min_dimension / min(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)

    # Grayscale
    img = img.convert("L")

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Contrast enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)

    return img


# ── Plain text ────────────────────────────────────────────────────────────────

def _extract_text(file_bytes: bytes) -> ExtractionResult:
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            return ExtractionResult(
                text=_clean_text(text), method="text", confidence=None
            )
        except (UnicodeDecodeError, LookupError):
            continue

    return ExtractionResult(
        text="", method="text", confidence=None, success=False,
        error_message="Could not decode the text file. Please save it as UTF-8 and re-upload.",
    )


# ── Utilities ─────────────────────────────────────────────────────────────────

def _clean_text(text: str) -> str:
    """Remove excess whitespace while preserving paragraph breaks."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        cleaned.append(stripped)
    # Collapse runs of blank lines to a single blank line
    result = []
    prev_blank = False
    for line in cleaned:
        if line == "":
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False
    return "\n".join(result).strip()
