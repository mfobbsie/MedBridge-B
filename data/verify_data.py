"""
medbridge-data/verify_data.py

Quick sanity check — prints row counts for every clinical table
so you can confirm data loaded correctly after running either
synthea_loader.py or fhir_mapper.py.

Usage:
  python verify_data.py
  python verify_data.py --user-id <uuid>   # filter to one user
"""

import argparse
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

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


def verify(user_id: str = None):
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise EnvironmentError("DATABASE_URL not set in .env")

    conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
    print("\nMedBridge DB — Row Counts")
    print("=" * 40)

    with conn.cursor() as cur:
        for table in TABLES:
            try:
                if user_id:
                    cur.execute(f"SELECT COUNT(*) as n FROM {table} WHERE user_id = %s",
                                (user_id,))
                else:
                    cur.execute(f"SELECT COUNT(*) as n FROM {table}")
                row = cur.fetchone()
                count = row["n"]
                print(f"  {table:<25} {count:>6} rows")
            except Exception as e:
                print(f"  {table:<25} ERROR: {e}")

    print("=" * 40)

    # Show breakdown by source_type
    print("\nhealth_records by source_type:")
    with conn.cursor() as cur:
        q = "SELECT source_type, COUNT(*) as n FROM health_records"
        params = []
        if user_id:
            q += " WHERE user_id = %s"
            params.append(user_id)
        q += " GROUP BY source_type ORDER BY source_type"
        cur.execute(q, params)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"  {row['source_type']:<15} {row['n']:>4} records")
        else:
            print("  (no records yet)")

    # Show lab flags breakdown
    print("\nlab_results by flag:")
    with conn.cursor() as cur:
        q = "SELECT flag, COUNT(*) as n FROM lab_results"
        params = []
        if user_id:
            q += " WHERE user_id = %s"
            params.append(user_id)
        q += " GROUP BY flag ORDER BY flag"
        cur.execute(q, params)
        rows = cur.fetchall()
        if rows:
            for row in rows:
                print(f"  {row['flag']:<12} {row['n']:>4}")
        else:
            print("  (no lab results yet)")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Verify MedBridge data loaded correctly.")
    parser.add_argument("--user-id", default=None,
        help="Filter counts to a specific Supabase user UUID")
    args = parser.parse_args()
    verify(args.user_id)


if __name__ == "__main__":
    main()
