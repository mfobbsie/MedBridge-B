"""
Standalone OCR test script.

Run this before the full server to verify Tesseract is working
and to see how the preprocessing pipeline handles your test images.

Usage:
    python scripts/test_ocr.py path/to/image.jpg
    python scripts/test_ocr.py path/to/image.png
    python scripts/test_ocr.py  # runs on a generated test image

Output:
    - Confidence score (0-100)
    - Whether low-confidence threshold was triggered
    - Extracted text
    - Any warnings
    - Saved preprocessed image (for debugging)

No .env or Supabase needed — pure local test.
"""

import sys
import io
import os
import pathlib

# ── Dependency check ──────────────────────────────────────────────────────────
missing = []
try:
    import pytesseract
except ImportError:
    missing.append("pytesseract")
try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
except ImportError:
    missing.append("Pillow")

if missing:
    print(f"\n❌  Missing packages: {', '.join(missing)}")
    print("    Run: pip install " + " ".join(missing))
    sys.exit(1)


# ── OCR confidence threshold (matches .env default) ───────────────────────────
OCR_CONFIDENCE_THRESHOLD = int(os.getenv("OCR_CONFIDENCE_THRESHOLD", "60"))


def preprocess_image(img: Image.Image) -> Image.Image:
    """Same pipeline as extraction_service.py."""
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Scale up small images to ~300 DPI equivalent
    min_dim = 1800
    if min(img.size) < min_dim:
        scale = min_dim / min(img.size)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.LANCZOS)
        print(f"   ↑  Scaled up to {new_size[0]}×{new_size[1]}")

    img = img.convert("L")                        # grayscale
    img = img.filter(ImageFilter.SHARPEN)         # sharpen
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)                   # boost contrast
    return img


def make_test_image() -> bytes:
    """Generate a synthetic lab-result-style image for testing."""
    img = Image.new("RGB", (800, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    lines = [
        "LABORATORY REPORT",
        "Patient: Test Patient",
        "Date: 2026-06-12",
        "",
        "COMPLETE BLOOD COUNT",
        "WBC: 7.2  [Normal: 4.5-11.0]",
        "RBC: 4.8  [Normal: 4.2-5.8]",
        "Hemoglobin: 14.2 g/dL  [Normal: 13.0-17.0]",
        "",
        "All results within normal limits.",
        "Follow up with your physician as scheduled.",
    ]

    y = 30
    for line in lines:
        size = 22 if line.isupper() else 18
        draw.text((40, y), line, fill=(0, 0, 0))
        y += size + 6

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run_ocr_test(image_path: str | None = None) -> None:
    print("\n" + "═" * 60)
    print("  MedBridge OCR Pipeline Test")
    print("═" * 60)

    # Load image
    if image_path:
        p = pathlib.Path(image_path)
        if not p.exists():
            print(f"\n❌  File not found: {image_path}")
            sys.exit(1)
        print(f"\n📄  Input: {p.name}  ({p.stat().st_size / 1024:.1f} KB)")
        file_bytes = p.read_bytes()
    else:
        print("\n📄  Input: generated synthetic lab result (no file provided)")
        file_bytes = make_test_image()

    img = Image.open(io.BytesIO(file_bytes))
    print(f"    Size: {img.width}×{img.height}  Mode: {img.mode}")

    # Preprocess
    print("\n🔧  Preprocessing...")
    preprocessed = preprocess_image(img)
    print(f"    Output size: {preprocessed.width}×{preprocessed.height}")

    # Save preprocessed image for inspection
    debug_path = pathlib.Path("ocr_debug_preprocessed.png")
    preprocessed.save(debug_path)
    print(f"    Saved preprocessed image → {debug_path}")

    # Run Tesseract with confidence data
    print("\n🔍  Running Tesseract...")
    try:
        ocr_data = pytesseract.image_to_data(
            preprocessed,
            output_type=pytesseract.Output.DICT,
            lang="eng",
        )
    except Exception as e:
        print(f"\n❌  Tesseract failed: {e}")
        print("    Check that Tesseract is installed: tesseract --version")
        sys.exit(1)

    # Calculate confidence
    confidences = [c for c in ocr_data["conf"] if c != -1]
    mean_conf = sum(confidences) / len(confidences) if confidences else 0
    low_conf_words = [
        (ocr_data["text"][i], ocr_data["conf"][i])
        for i in range(len(ocr_data["text"]))
        if ocr_data["conf"][i] != -1 and ocr_data["conf"][i] < 40 and ocr_data["text"][i].strip()
    ]

    # Extract text
    text = pytesseract.image_to_string(preprocessed, lang="eng").strip()

    # Report
    print(f"\n📊  Results")
    print(f"    Confidence:    {mean_conf:.1f} / 100")
    conf_bar = "█" * int(mean_conf / 5) + "░" * (20 - int(mean_conf / 5))
    print(f"    [{conf_bar}]")

    threshold_status = "✅  Above threshold" if mean_conf >= OCR_CONFIDENCE_THRESHOLD else "⚠️   Below threshold"
    print(f"    Threshold ({OCR_CONFIDENCE_THRESHOLD}): {threshold_status}")

    if low_conf_words:
        print(f"\n⚠️   Low-confidence words ({len(low_conf_words)}):")
        for word, conf in low_conf_words[:10]:
            print(f"    '{word}' ({conf}%)")
        if len(low_conf_words) > 10:
            print(f"    ... and {len(low_conf_words) - 10} more")

    char_count = len(text.strip())
    word_count = len(text.split())
    print(f"\n📝  Extracted text")
    print(f"    {word_count} words, {char_count} characters")
    print(f"\n{'─' * 60}")
    if text:
        # Show first 800 chars
        preview = text[:800]
        print(preview)
        if len(text) > 800:
            print(f"\n    ... ({len(text) - 800} more characters)")
    else:
        print("    (no text extracted)")
    print(f"{'─' * 60}")

    # Warnings (same logic as extraction_service.py)
    warnings = []
    if mean_conf < OCR_CONFIDENCE_THRESHOLD:
        warnings.append(
            f"Confidence was {mean_conf:.0f}% (below {OCR_CONFIDENCE_THRESHOLD}% threshold). "
            "For best results, use a well-lit, flat photo or a PDF."
        )
    if char_count < 50:
        warnings.append(
            "Very little text was found. The image may be too blurry, "
            "low-contrast, or contain mostly graphics rather than text."
        )

    if warnings:
        print(f"\n⚠️   Warnings that would be shown to the user:")
        for w in warnings:
            print(f"    • {w}")
    else:
        print(f"\n✅  No warnings — this image would process cleanly")

    print("\n" + "═" * 60 + "\n")


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    run_ocr_test(image_path)
