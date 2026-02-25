"""
Backfill Euromillones only (1999 to end_date).
Run: python scripts/backfill_euromillones.py
Failed ranges only: python scripts/backfill_euromillones.py --only 20150701-20151231 20170101-20170630 20190701-20191231
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backfill_common import parse_only_ranges, run_backfill

if __name__ == "__main__":
    only = parse_only_ranges(sys.argv)
    run_backfill("euromillones", only)
    print("Backfill done.")
