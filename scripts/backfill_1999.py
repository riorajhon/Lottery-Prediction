"""
Backfill is split into one script per lottery. Run each as needed:

  python scripts/backfill_la_primitiva.py
  python scripts/backfill_euromillones.py
  python scripts/backfill_el_gordo.py

Failed ranges only (example):
  python scripts/backfill_la_primitiva.py --only 20210101-20210630 20110701-20111231

Daily update (00:02) is combined: one run scrapes Euromillones → La Primitiva → El Gordo
(via POST /api/scrape/daily or scripts/run_daily_scrape.py).
"""
import sys
if __name__ == "__main__":
    print(__doc__.strip())
    sys.exit(0)
