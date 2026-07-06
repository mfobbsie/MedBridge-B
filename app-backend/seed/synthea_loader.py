"""
medbridge-db/seed/synthea_loader.py

Loads a Synthea-generated FHIR R4 bundle into the MedBridge normalized schema.

Why this exists:
  - Gives the entire team realistic clinical data to build against from Day 1
  - Validates the normalized schema before any real FHIR data arrives
  - Uses the SAME parsing logic as the real FHIR integration (fhir_mapper.py),
    so fixing a parsing bug here fixes it everywhere
  - Seeds the DB without anyone needing a real Epic account

How to run:
  python synthea_loader.py --user-id <uuid> --bundle path/to/bundle.json
  python synthea_loader.py --user-id <uuid> --dir   path/to/synthea/output/fhir/

Get Synthea from: https://github.com/synthetichealth/synthea/releases
Run it:           java -jar synthea-with-dependencies.jar -p 5
Output is in:     output/fhir/*.json (each file is one patient bundle)
"""

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Allow `from app...` when run as `python seed/synthea_loader.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_backend_root = Path(__file__).resolve().parents[1]
load_dotenv(_backend_root / ".env")
load_dotenv(_backend_root.parent / ".env")

# ---------------------------------------------------------------------------
# DB connection
# ---------------------------------------------------------------------------
def get_supabase_client():
    """Service-role Supabase client (bypasses RLS). Used when direct Postgres is unreachable."""
    from app.database import get_supabase
    return get_supabase()


def _serialize_row(row: dict) -> dict:
    """Convert values for Supabase REST insert (e.g. datetime â†’ ISO string)."""
    allowed_flags = {"normal", "low", "high", "critical"}
    out = {}
    for key, value in row.items():
        if key == "flag" and value not in allowed_flags:
            value = None
        if isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


# ---------------------------------------------------------------------------
# FHIR helpers â€” defensive accessors, never crash on missing fields
# ---------------------------------------------------------------------------
def coding_first(codeable_concept: dict, field="coding") -> dict:
    """Return the first coding entry from a CodeableConcept, or {}."""
    return (codeable_concept or {}).get(field, [{}])[0] or {}


def text_or_display(codeable_concept: dict) -> Optional[str]:
    """Best display string from a CodeableConcept."""
    if not codeable_concept:
        return None
    return codeable_concept.get("text") or coding_first(codeable_concept).get("display")


def parse_date(dt_str: Optional[str]) -> Optional[str]:
    """Coerce FHIR dateTime / date / Period.start to a date string YYYY-MM-DD."""
    if not dt_str:
        return None
    return dt_str[:10]  # ISO date is always the first 10 chars


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Coerce FHIR dateTime to a UTC-aware datetime."""
    if not dt_str:
        return None
    try:
        # FHIR datetimes may or may not have timezone; normalize to UTC
        s = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Per-resource parsers
# Each returns a dict ready to INSERT, or None if the resource should be skipped.
# ---------------------------------------------------------------------------

def parse_condition(res: dict, health_record_id: str, user_id: str) -> Optional[dict]:
    code_cc = res.get("code", {})
    coding = coding_first(code_cc)
    status_cc = res.get("clinicalStatus", {})
    status_code = coding_first(status_cc).get("code", "unknown")

    # Map FHIR clinical status codes to our simpler set
    status_map = {"active": "active", "resolved": "resolved",
                  "inactive": "inactive", "remission": "resolved"}
    status = status_map.get(status_code, "unknown")

    name = text_or_display(code_cc)
    if not name:
        return None  # skip conditions with no name

    return {
        "id": str(uuid.uuid4()),
        "health_record_id": health_record_id,
        "user_id": user_id,
        "name": name,
        "code": coding.get("code"),
        "code_system": _friendly_system(coding.get("system")),
        "status": status,
        "onset_date": parse_date(res.get("onsetDateTime") or
                                  res.get("onsetPeriod", {}).get("start")),
    }


def parse_medication_request(res: dict, health_record_id: str, user_id: str) -> Optional[dict]:
    med_cc = res.get("medicationCodeableConcept", {})
    coding = coding_first(med_cc)
    name = text_or_display(med_cc)
    if not name:
        return None

    dosage = (res.get("dosageInstruction") or [{}])[0]
    dose_text = dosage.get("text", "")
    # Try to pull dose + frequency out of the single dosage text string
    # (Synthea puts them together: "Take 1 tablet daily")
    dose, frequency = dose_text, None
    for sep in [" once", " twice", " daily", " weekly", " every"]:
        if sep in dose_text.lower():
            idx = dose_text.lower().index(sep)
            dose = dose_text[:idx].strip()
            frequency = dose_text[idx:].strip()
            break

    fhir_status = res.get("status", "unknown")
    status_map = {"active": "active", "stopped": "stopped",
                  "completed": "stopped", "on-hold": "on-hold"}

    return {
        "id": str(uuid.uuid4()),
        "health_record_id": health_record_id,
        "user_id": user_id,
        "name": name,
        "code": coding.get("code"),
        "code_system": _friendly_system(coding.get("system")),
        "dose": dose or None,
        "frequency": frequency,
        "status": status_map.get(fhir_status, "unknown"),
    }


def parse_observation(res: dict, health_record_id: str, user_id: str) -> Optional[dict]:
    """Only process laboratory observations."""
    categories = res.get("category", [])
    is_lab = any(
        coding_first(cat).get("code") == "laboratory"
        for cat in categories
    )
    if not is_lab:
        return None

    code_cc = res.get("code", {})
    coding = coding_first(code_cc)
    name = text_or_display(code_cc)
    if not name:
        return None

    # Value â€” FHIR uses valueQuantity, valueString, valueCodeableConcept, etc.
    value_quantity = None
    value_text = None
    unit = None

    if "valueQuantity" in res:
        vq = res["valueQuantity"]
        value_quantity = vq.get("value")
        value_text = str(value_quantity) if value_quantity is not None else None
        unit = vq.get("unit") or vq.get("code")
    elif "valueString" in res:
        value_text = res["valueString"]
    elif "valueCodeableConcept" in res:
        value_text = text_or_display(res["valueCodeableConcept"])

    # Reference range
    rr = (res.get("referenceRange") or [{}])[0]
    rr_low = (rr.get("low") or {}).get("value")
    rr_high = (rr.get("high") or {}).get("value")
    rr_text = rr.get("text")

    # Flag from interpretation
    interp = coding_first((res.get("interpretation") or [{}])[0]).get("code", "")
    flag_map = {"N": "normal", "H": "high", "L": "low", "HH": "critical",
                "LL": "critical", "A": "unknown"}
    flag = flag_map.get(interp.upper(), "unknown")

    # Infer flag from range if interpretation absent
    if flag == "unknown" and value_quantity is not None:
        if rr_low is not None and value_quantity < rr_low:
            flag = "low"
        elif rr_high is not None and value_quantity > rr_high:
            flag = "high"
        elif rr_low is not None and rr_high is not None:
            flag = "normal"

    if flag == "unknown":
        flag = None

    effective = res.get("effectiveDateTime") or \
                (res.get("effectivePeriod") or {}).get("start")

    return {
        "id": str(uuid.uuid4()),
        "health_record_id": health_record_id,
        "user_id": user_id,
        "name": name,
        "code": coding.get("code"),
        "code_system": _friendly_system(coding.get("system")),
        "value_quantity": value_quantity,
        "value_text": value_text,
        "unit": unit,
        "reference_range_low": rr_low,
        "reference_range_high": rr_high,
        "reference_range_text": rr_text,
        "flag": flag,
        "observed_at": parse_datetime(effective),
    }


def parse_encounter(res: dict, health_record_id: str, user_id: str) -> Optional[dict]:
    enc_types = res.get("type", [{}])
    enc_type = text_or_display(enc_types[0]) if enc_types else None

    reason = res.get("reasonCode", [{}])
    description = text_or_display(reason[0]) if reason else None

    participant = (res.get("participant") or [{}])[0]
    provider = (participant.get("individual") or {}).get("display")

    service_provider = (res.get("serviceProvider") or {}).get("display")
    period = res.get("period") or {}

    return {
        "id": str(uuid.uuid4()),
        "health_record_id": health_record_id,
        "user_id": user_id,
        "encounter_type": enc_type,
        "description": description,
        "provider": provider,
        "facility": service_provider,
        "occurred_at": parse_datetime(period.get("start")),
    }


def parse_allergy(res: dict, health_record_id: str, user_id: str) -> Optional[dict]:
    substance_cc = res.get("code") or (res.get("reaction") or [{}])[0].get("substance", {})
    substance = text_or_display(substance_cc)
    if not substance:
        return None

    reactions = res.get("reaction") or []
    reaction_text = None
    severity = "unknown"
    if reactions:
        r = reactions[0]
        manifestations = r.get("manifestation") or []
        if manifestations:
            reaction_text = text_or_display(manifestations[0])
        severity = r.get("severity", "unknown")
        if severity not in ("mild", "moderate", "severe"):
            severity = "unknown"

    status_code = coding_first(res.get("clinicalStatus", {})).get("code", "active")
    status_map = {"active": "active", "inactive": "inactive", "resolved": "resolved"}
    status = status_map.get(status_code, "active")

    return {
        "id": str(uuid.uuid4()),
        "health_record_id": health_record_id,
        "user_id": user_id,
        "substance": substance,
        "reaction": reaction_text,
        "severity": severity,
        "status": status,
    }


def _friendly_system(uri: Optional[str]) -> Optional[str]:
    """Map FHIR system URIs to friendly names for our code_system column."""
    if not uri:
        return None
    mapping = {
        "http://snomed.info/sct": "SNOMED-CT",
        "http://hl7.org/fhir/sid/icd-10-cm": "ICD-10-CM",
        "http://hl7.org/fhir/sid/icd-9-cm": "ICD-9-CM",
        "http://www.nlm.nih.gov/research/umls/rxnorm": "RxNorm",
        "http://loinc.org": "LOINC",
    }
    return mapping.get(uri, uri)


# ---------------------------------------------------------------------------
# Bundle loader
# ---------------------------------------------------------------------------
PARSERS = {
    "Condition":          parse_condition,
    "MedicationRequest":  parse_medication_request,
    "Observation":        parse_observation,
    "Encounter":          parse_encounter,
    "AllergyIntolerance": parse_allergy,
}

TABLES = {
    "Condition":          "conditions",
    "MedicationRequest":  "medications",
    "Observation":        "lab_results",
    "Encounter":          "encounters",
    "AllergyIntolerance": "allergies",
}


def load_bundle(bundle_path: Path, user_id: str, supabase) -> dict:
    """Parse one Synthea FHIR bundle and insert into the normalized schema.
    Returns a summary dict of counts."""
    with open(bundle_path, encoding='utf-8', errors='replace') as f:
        bundle = json.load(f)

    entries = bundle.get("entry", [])
    if not entries:
        print(f"  WARNING: {bundle_path.name} has no entries â€” skipping.")
        return {}

    # Extract Patient name for display_name
    patient_name = bundle_path.stem  # fallback: filename
    for entry in entries:
        res = entry.get("resource", {})
        if res.get("resourceType") == "Patient":
            names = res.get("name", [{}])
            n = names[0] if names else {}
            given = " ".join(n.get("given", []))
            family = n.get("family", "")
            if given or family:
                patient_name = f"{given} {family}".strip()
            break

    counts = {rt: 0 for rt in PARSERS}

    # Create the health_record for this bundle
    hr_id = str(uuid.uuid4())
    supabase.table("health_records").insert({
        "id": hr_id,
        "user_id": user_id,
        "source_type": "synthea",
        "display_name": f"Synthetic patient â€” {patient_name}",
        "status": "ready",
    }).execute()

    # Parse and insert each resource
    for entry in entries:
        res = entry.get("resource", {})
        rt = res.get("resourceType")
        if rt not in PARSERS:
            continue

        row = PARSERS[rt](res, hr_id, user_id)
        if row is None:
            continue

        table = TABLES[rt]
        supabase.table(table).insert(_serialize_row(row)).execute()
        counts[rt] += 1

    return {"health_record_id": hr_id, "patient_name": patient_name, "counts": counts}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Load Synthea FHIR bundles into the MedBridge normalized schema."
    )
    parser.add_argument("--user-id", required=True,
        help="Supabase user UUID to assign records to. Get this from the Supabase "
             "Auth dashboard after creating a test user, or from auth.users in the "
             "SQL editor: SELECT id FROM auth.users LIMIT 5;")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--bundle", type=Path,
        help="Path to a single Synthea FHIR bundle JSON file.")
    group.add_argument("--dir", type=Path,
        help="Directory of Synthea FHIR bundle JSON files (loads all *.json).")
    args = parser.parse_args()

    supabase = get_supabase_client()
    print(f"Connected to Supabase. Loading records for user {args.user_id}\n")

    bundles = [args.bundle] if args.bundle else sorted(args.dir.glob("*.json"))
    if not bundles:
        print("No JSON files found.")
        return

    total_counts = {rt: 0 for rt in PARSERS}
    loaded = 0
    for bundle_path in bundles:
        print(f"Loading {bundle_path.name}...")
        try:
            result = load_bundle(bundle_path, args.user_id, supabase)
        except Exception as e:
            print(f"  WARNING: skipped {bundle_path.name} â€” {e}")
            continue
        if result:
            loaded += 1
            c = result["counts"]
            print(f"  OK {result['patient_name']} (health_record: {result['health_record_id']})")
            print(f"    conditions={c['Condition']} medications={c['MedicationRequest']} "
                  f"labs={c['Observation']} encounters={c['Encounter']} "
                  f"allergies={c['AllergyIntolerance']}")
            for rt in PARSERS:
                total_counts[rt] += c[rt]

    print(f"\n{'='*50}")
    print(f"Done. Loaded {loaded} bundle(s).")
    print(f"Total: conditions={total_counts['Condition']} "
          f"medications={total_counts['MedicationRequest']} "
          f"labs={total_counts['Observation']} "
          f"encounters={total_counts['Encounter']} "
          f"allergies={total_counts['AllergyIntolerance']}")


if __name__ == "__main__":
    main()
