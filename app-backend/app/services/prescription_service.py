"""
Prescription classification and medication extraction.

Uses Groq vision for images/PDF first pages, with OCR/text LLM fallback.
Failures are non-fatal for callers (upload still succeeds).
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from groq import Groq
from pydantic import BaseModel, Field, field_validator, model_validator
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.summary_service import _truncate_to_limit

logger = logging.getLogger(__name__)

PRESCRIPTION_SYSTEM_PROMPT = """You are MedBridge, a healthcare document understanding tool.

Your task is to decide whether the DOCUMENT is a prescription (or prescription
label / Rx fill / medication order), and if so extract the medications listed.

Rules:
1. Base answers ONLY on information in the document. Never invent drugs or doses.
2. Set is_prescription to true only if the document clearly looks like a prescription,
   Rx label, pharmacy fill, or medication order (e.g. drug name + dose/Sig, Rx number,
   "Rx", "Sig:", "dispense", "refills", prescribing provider).
3. Lab results, discharge summaries, imaging reports, insurance letters, and general
   visit notes that merely mention a drug in passing are NOT prescriptions —
   set is_prescription false and medications to [].
4. If is_prescription is false, medications MUST be an empty array.
5. For each medication, include only fields supported by the document; use null for unknown.
6. Dates must be YYYY-MM-DD strings when known, otherwise null.
7. Return ONLY valid JSON. No preamble, no markdown fences.
   Format:
   {
     "is_prescription": true,
     "medications": [
       {
         "name": "Lisinopril",
         "dosage": "10 mg",
         "frequency": "once daily",
         "route": "oral",
         "prescribing_provider": "Dr. Smith",
         "start_date": "2026-07-22",
         "end_date": null,
         "reason": null,
         "notes": "Take with food"
       }
     ]
   }"""


def normalize_date(value: Optional[str]) -> Optional[str]:
    """Coerce common date strings to YYYY-MM-DD, or return None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ("null", "none", "n/a", "unknown"):
        return None

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        try:
            datetime.strptime(text, "%Y-%m-%d")
            return text
        except ValueError:
            return None

    # Strip time portion from ISO timestamps
    if "T" in text:
        text = text.split("T", 1)[0].strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            try:
                datetime.strptime(text, "%Y-%m-%d")
                return text
            except ValueError:
                return None

    for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%d/%m/%Y", "%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


class ExtractedMedicationCandidate(BaseModel):
    name: str = Field(..., min_length=1)
    dose: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    prescribing_provider: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None

    @model_validator(mode="after")
    def sync_dose_dosage(self) -> ExtractedMedicationCandidate:
        if self.dosage and not self.dose:
            self.dose = self.dosage
        elif self.dose and not self.dosage:
            self.dosage = self.dose
        self.start_date = normalize_date(self.start_date)
        self.end_date = normalize_date(self.end_date)
        return self

    def to_pending_row(self) -> dict:
        return {
            "name": self.name.strip(),
            "dose": (self.dose or self.dosage or None),
            "frequency": self.frequency,
            "route": self.route,
            "prescribing_provider": self.prescribing_provider,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "reason": self.reason,
            "notes": self.notes,
        }

    def to_extracted_data(self) -> dict:
        return {
            "name": self.name.strip(),
            "dosage": self.dosage or self.dose,
            "frequency": self.frequency,
            "route": self.route,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "prescribing_provider": self.prescribing_provider,
            "reason": self.reason,
            "notes": self.notes,
        }


class PrescriptionExtractionPayload(BaseModel):
    is_prescription: bool = False
    medications: list[ExtractedMedicationCandidate] = Field(default_factory=list)

    @field_validator("medications", mode="before")
    @classmethod
    def coerce_medications(cls, value):
        if value is None:
            return []
        return value


@dataclass
class PrescriptionExtractionResult:
    is_prescription: bool = False
    medications: list[ExtractedMedicationCandidate] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None

    def primary_extracted_data(self) -> Optional[dict]:
        if not self.is_prescription or not self.medications:
            return None
        return self.medications[0].to_extracted_data()

    def pending_rows(self) -> list[dict]:
        if not self.is_prescription:
            return []
        return [m.to_pending_row() for m in self.medications]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def _call_groq(client: Groq, model: str, messages: list[dict], max_tokens: int = 800) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.1,
    )
    return (response.choices[0].message.content or "").strip()


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.lstrip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def _parse_payload(raw: str) -> PrescriptionExtractionResult:
    parsed = json.loads(_strip_json_fences(raw))
    payload = PrescriptionExtractionPayload.model_validate(parsed)
    meds = [m for m in payload.medications if m.name and m.name.strip()]
    is_rx = bool(payload.is_prescription) and len(meds) > 0
    return PrescriptionExtractionResult(
        is_prescription=is_rx,
        medications=meds if is_rx else [],
    )


def _pdf_first_page_png(file_bytes: bytes) -> Optional[bytes]:
    try:
        import fitz

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        if doc.page_count < 1:
            doc.close()
            return None
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        png_bytes = pix.tobytes("png")
        doc.close()
        return png_bytes
    except Exception as e:
        logger.warning("PDF page render failed: %s", e)
        return None


def _image_to_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
    # Cap base64 payload roughly under Groq's 4MB base64 guidance by shrinking if needed
    data = image_bytes
    if len(base64.b64encode(data)) > 3_500_000:
        try:
            from PIL import Image

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


def _extract_via_vision(image_bytes: bytes, mime_type: str = "image/png") -> PrescriptionExtractionResult:
    settings = get_settings()
    if not settings.groq_api_key:
        return PrescriptionExtractionResult(
            success=False,
            error_message="AI service is not configured.",
        )

    client = Groq(api_key=settings.groq_api_key)
    data_url = _image_to_data_url(image_bytes, mime_type)
    messages = [
        {"role": "system", "content": PRESCRIPTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Classify whether this document image is a prescription and "
                        "extract medications as JSON."
                    ),
                },
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        },
    ]
    raw = ""
    try:
        raw = _call_groq(client, settings.groq_vision_model, messages, max_tokens=1000)
        return _parse_payload(raw)
    except json.JSONDecodeError as e:
        logger.warning("Vision prescription JSON parse failed: %s — raw: %s", e, raw[:200])
        return PrescriptionExtractionResult(
            success=False,
            error_message="Could not parse prescription extraction response.",
        )
    except Exception as e:
        logger.exception("Vision prescription extraction failed: %s", e)
        return PrescriptionExtractionResult(
            success=False,
            error_message="Unable to extract medications from this document.",
        )


def extract_prescription_medications(extracted_text: str) -> PrescriptionExtractionResult:
    """Text-only fallback used by OCR pipeline and TXT uploads."""
    settings = get_settings()

    if not extracted_text or not extracted_text.strip():
        return PrescriptionExtractionResult(
            success=False,
            error_message="No document text available for prescription extraction.",
        )

    if not settings.groq_api_key:
        logger.warning("Groq API key missing — skipping prescription extraction")
        return PrescriptionExtractionResult(
            success=False,
            error_message="AI service is not configured.",
        )

    context = _truncate_to_limit(extracted_text, settings.max_context_tokens - 200)
    client = Groq(api_key=settings.groq_api_key)
    messages = [
        {"role": "system", "content": PRESCRIPTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"DOCUMENT:\n{context}\n\n"
                "Classify whether this is a prescription and extract medications as JSON."
            ),
        },
    ]

    raw = ""
    try:
        raw = _call_groq(client, settings.groq_model, messages)
        return _parse_payload(raw)
    except json.JSONDecodeError as e:
        logger.warning("Prescription JSON parse failed: %s — raw: %s", e, raw[:200])
        return PrescriptionExtractionResult(
            success=False,
            error_message="Could not parse prescription extraction response.",
        )
    except Exception as e:
        logger.exception("Prescription extraction failed: %s", e)
        return PrescriptionExtractionResult(
            success=False,
            error_message="Unable to extract medications from this document.",
        )


def analyze_prescription_file(file_bytes: bytes, mime_type: str) -> PrescriptionExtractionResult:
    """
    Classify/extract from an uploaded file.
    Prefers vision for images and PDF first page; falls back to text OCR LLM.
    """
    mime = (mime_type or "").lower()

    if mime in ("image/png", "image/jpeg"):
        result = _extract_via_vision(file_bytes, mime)
        if result.success:
            return result
        logger.info("Vision failed for image; falling back to OCR text extraction")
        from app.services.extraction_service import extract_text

        extraction = extract_text(file_bytes, mime)
        if extraction.success and extraction.text:
            return extract_prescription_medications(extraction.text)
        return result

    if mime == "application/pdf":
        png = _pdf_first_page_png(file_bytes)
        if png:
            result = _extract_via_vision(png, "image/png")
            if result.success:
                return result
            logger.info("Vision failed for PDF page; falling back to text extraction")
        from app.services.extraction_service import extract_text

        extraction = extract_text(file_bytes, mime)
        if extraction.success and extraction.text:
            return extract_prescription_medications(extraction.text)
        return PrescriptionExtractionResult(
            success=False,
            error_message="Unable to analyze PDF for prescription data.",
        )

    if mime == "text/plain":
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")
        return extract_prescription_medications(text)

    return PrescriptionExtractionResult(
        success=False,
        error_message=f"Unsupported mime type for prescription analysis: {mime_type}",
    )
