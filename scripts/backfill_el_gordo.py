"""
Backfill El Gordo only (1999 to end_date).
Run: python scripts/backfill_el_gordo.py
Failed ranges only: python scripts/backfill_el_gordo.py --only 20060101-20060630 20210701-20211231 20220701-20221231
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backfill_common import parse_only_ranges, run_backfill

if __name__ == "__main__":
    only = parse_only_ranges(sys.argv)
    run_backfill("el-gordo", only)
    print("Backfill done.")
