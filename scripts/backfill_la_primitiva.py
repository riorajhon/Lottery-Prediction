"""
Backfill La Primitiva only (1999 to end_date).
Run: python scripts/backfill_la_primitiva.py
Failed ranges only: python scripts/backfill_la_primitiva.py --only 20210101-20210630 20110701-20111231
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backfill_common import parse_only_ranges, run_backfill

if __name__ == "__main__":
    only = parse_only_ranges(sys.argv)
    run_backfill("la-primitiva", only)
    print("Backfill done.")
