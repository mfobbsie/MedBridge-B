"""
medbridge-data/verify_data.py

Quick sanity check â€” prints row counts for every clinical table
so you can confirm data loaded correctly after running either
synthea_loader.py or fhir_mapper.py.

Usage:
  python data/verify_data.py
  python data/verify_data.py --user-id <uuid>   # filter to one user
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv

_backend_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_backend_root))
load_dotenv(_backend_root / ".env")
load_dotenv(_backend_root.parent / ".env")

TABLES = [
    "health_records",
    "fhir_connections",
    "conditions",
    "medications",
    "lab_results",
    "encounters",
    "follow_ups",
    "allergies",
    "summaries",
    "chat_messages",
]


def _count_table(supabase, table: str, user_id: str | None) -> int:
    query = supabase.table(table).select("id", count="exact")
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.execute()
    return result.count or 0


def _fetch_column(supabase, table: str, column: str, user_id: str | None) -> list:
    query = supabase.table(table).select(column)
    if user_id:
        query = query.eq("user_id", user_id)
    result = query.execute()
    return [row[column] for row in (result.data or [])]


def verify(user_id: str = None):
    from app.database import get_supabase

    supabase = get_supabase()
    print("\nMedBridge DB â€” Row Counts")
    print("=" * 40)

    for table in TABLES:
        try:
            count = _count_table(supabase, table, user_id)
            print(f"  {table:<25} {count:>6} rows")
        except Exception as e:
            print(f"  {table:<25} ERROR: {e}")

    print("=" * 40)

    print("\nhealth_records by source_type:")
    try:
        source_types = _fetch_column(supabase, "health_records", "source_type", user_id)
        if source_types:
            for source_type, n in sorted(Counter(source_types).items()):
                print(f"  {source_type:<15} {n:>4} records")
        else:
            print("  (no records yet)")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\nlab_results by flag:")
    try:
        flags = _fetch_column(supabase, "lab_results", "flag", user_id)
        if flags:
            for flag, n in sorted(Counter(flags).items(), key=lambda x: (x[0] is None, x[0] or "")):
                label = flag if flag is not None else "(null)"
                print(f"  {label:<12} {n:>4}")
        else:
            print("  (no lab results yet)")
    except Exception as e:
        print(f"  ERROR: {e}")


def main():
    parser = argparse.ArgumentParser(description="Verify MedBridge data loaded correctly.")
    parser.add_argument("--user-id", default=None,
        help="Filter counts to a specific Supabase user UUID")
    args = parser.parse_args()
    verify(args.user_id)


if __name__ == "__main__":
    main()
