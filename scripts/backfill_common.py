"""
Shared backfill logic for lottery history (1999 to end_date).
Used by backfill_la_primitiva.py, backfill_euromillones.py, backfill_el_gordo.py.
"""
import os
import re
import sys
import time
from datetime import datetime

# Load .env from project root or backend
_scripts_dir = os.path.dirname(os.path.abspath(__file__))
for _path in [
    os.path.join(_scripts_dir, "..", "backend", ".env"),
    os.path.join(_scripts_dir, "..", ".env"),
]:
    if os.path.isfile(_path):
        with open(_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k.strip() and k.strip() not in os.environ:
                        os.environ[k.strip()] = v.strip()
        break

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "lottery")
METADATA_COLLECTION = "scraper_metadata"

GAME_IDS = {"la-primitiva": "LAPR", "euromillones": "EMIL", "el-gordo": "ELGR"}
COLLECTIONS = {"LAPR": "la_primitiva", "EMIL": "euromillones", "ELGR": "el_gordo"}
RESULTS_PATHS = {
    "la-primitiva": "/es/resultados/la-primitiva",
    "euromillones": "/es/resultados/euromillones",
    "el-gordo": "/es/resultados/gordo-primitiva",
}
BASE_URL = "https://www.loteriasyapuestas.es/servicios/buscadorSorteos"
SITE_ORIGIN = "https://www.loteriasyapuestas.es"
DELAY_BETWEEN_REQUESTS = 2.5
# Same order as backend: Euromillones → La Primitiva → El Gordo
LOTTERY_DAILY_ORDER = ["euromillones", "la-primitiva", "el-gordo"]


def parse_combinacion(combinacion: str) -> dict:
    numbers = []
    complementario = reintegro = None
    if not combinacion or not isinstance(combinacion, str):
        return {"numbers": numbers, "complementario": complementario, "reintegro": reintegro}
    match_c = re.search(r"C\((\d+)\)", combinacion)
    match_r = re.search(r"R\((\d+)\)", combinacion)
    if match_c:
        complementario = int(match_c.group(1))
    if match_r:
        reintegro = int(match_r.group(1))
    main_part = re.split(r"\s+C\(|\s+R\(", combinacion)[0].strip()
    for part in main_part.split("-"):
        part = part.strip()
        if part.isdigit():
            numbers.append(int(part))
    return {"numbers": numbers, "complementario": complementario, "reintegro": reintegro}


def normalize_draw(draw: dict) -> dict:
    out = dict(draw)
    parsed = parse_combinacion(draw.get("combinacion") or "")
    out["numbers"] = parsed["numbers"]
    out["complementario"] = parsed["complementario"]
    out["reintegro"] = parsed["reintegro"]
    joker = draw.get("joker") or {}
    millon = draw.get("millon") or {}
    out["joker_combinacion"] = (
        (joker.get("combinacion") if isinstance(joker, dict) else None)
        or (millon.get("combinacion") if isinstance(millon, dict) else None)
    )
    return out


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
    if sys.platform.startswith("linux"):
        options.add_argument("--disable-setuid-sandbox")
        try:
            import shutil
            for path in ("/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"):
                if shutil.which(path):
                    options.binary_location = path
                    break
        except Exception:
            pass
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    driver.set_script_timeout(30)
    return driver


def fetch_range(api_url: str, results_page_url: str) -> list:
    driver = None
    try:
        driver = create_driver()
        driver.get(results_page_url)
        data = driver.execute_async_script(
            """
            var url = arguments[0];
            var callback = arguments[arguments.length - 1];
            fetch(url).then(function(r){ if(!r.ok) throw new Error('HTTP '+r.status); return r.json(); }).then(callback).catch(function(e){ callback({__error: e.message}); });
            """,
            api_url,
        )
        if isinstance(data, dict) and data.get("__error"):
            raise RuntimeError(data["__error"])
        if isinstance(data, dict) and data.get("id_sorteo"):
            data = [data]
        return data if isinstance(data, list) else []
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def save_draws(db, game_id: str, data: list) -> int:
    saved = 0
    coll_name = COLLECTIONS.get(game_id)
    if not coll_name:
        return 0
    for draw in data:
        if not isinstance(draw, dict):
            continue
        draw_id = draw.get("id_sorteo")
        if not draw_id:
            continue
        try:
            doc = normalize_draw(draw)
            db[coll_name].replace_one({"id_sorteo": draw_id}, doc, upsert=True)
            saved += 1
        except PyMongoError:
            pass
    return saved


def get_max_draw_date(db, game_id: str) -> str | None:
    coll_name = COLLECTIONS.get(game_id)
    if not coll_name:
        return None
    doc = db[coll_name].find_one(sort=[("fecha_sorteo", -1)], projection={"fecha_sorteo": 1})
    if not doc or not doc.get("fecha_sorteo"):
        return None
    return (doc["fecha_sorteo"] or "").split(" ")[0]


def set_last_draw_date(db, lottery_slug: str, date_str: str):
    db[METADATA_COLLECTION].update_one(
        {"lottery": lottery_slug},
        {"$set": {"last_draw_date": date_str}},
        upsert=True,
    )


def get_last_draw_date_from_metadata(db, lottery_slug: str) -> str | None:
    """Get last_draw_date for a lottery from scraper_metadata."""
    doc = db[METADATA_COLLECTION].find_one({"lottery": lottery_slug}, projection=["last_draw_date"])
    return (doc.get("last_draw_date") or "").strip() or None if doc else None


def max_date_from_draws(data: list) -> str | None:
    """Return max fecha_sorteo date (YYYY-MM-DD) from a list of draws."""
    out = None
    for draw in data:
        if not isinstance(draw, dict):
            continue
        f = (draw.get("fecha_sorteo") or "").strip()
        if f:
            d = f.split(" ")[0]
            if d and (out is None or d > out):
                out = d
    return out


def run_daily() -> list[dict]:
    """
    Run daily scrape for all lotteries (Euromillones → La Primitiva → El Gordo).
    Scrape window: 3 days ago → today. Saves/updates draws in DB; updates last_draw_date.
    Uses Selenium + MongoDB directly; no HTTP call. Returns list of result dicts.
    """
    from datetime import timedelta
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    today = datetime.now().strftime("%Y-%m-%d")
    today_yyyymmdd = today.replace("-", "")
    from_d = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_yyyymmdd = from_d.replace("-", "")
    results = []
    for lottery in LOTTERY_DAILY_ORDER:
        game_id = GAME_IDS.get(lottery)
        if not game_id:
            continue
        last_in_db = get_max_draw_date(db, game_id)
        print(f"  {lottery}: last history date (from DB) = {last_in_db or '(none)'}")
        if start_yyyymmdd > today_yyyymmdd:
            results.append({"lottery": lottery, "saved": 0, "message": "Already up to date"})
            print(f"  {lottery}: Already up to date")
            continue
        api_url = (
            f"{BASE_URL}?game_id={game_id}&celebrados=true"
            f"&fechaInicioInclusiva={start_yyyymmdd}&fechaFinInclusiva={today_yyyymmdd}"
        )
        results_path = RESULTS_PATHS.get(lottery, RESULTS_PATHS["la-primitiva"])
        results_page_url = f"{SITE_ORIGIN}{results_path}"
        try:
            data = fetch_range(api_url, results_page_url)
            if isinstance(data, dict) and data.get("id_sorteo"):
                data = [data]
            if not isinstance(data, list):
                results.append({"lottery": lottery, "saved": 0, "message": "Invalid response"})
                print(f"  {lottery}: Invalid response")
                continue
            saved = save_draws(db, game_id, data)
            max_date = max_date_from_draws(data)
            if max_date:
                set_last_draw_date(db, lottery, max_date)
            msg = f"Saved {saved} draws"
            results.append({"lottery": lottery, "saved": saved, "message": msg})
            print(f"  {lottery}: {msg}")
        except Exception as e:
            results.append({"lottery": lottery, "saved": 0, "message": str(e)})
            print(f"  {lottery}: ERROR {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS)
    client.close()
    return results


def parse_only_ranges(argv: list) -> list[tuple[str, str]] | None:
    """Parse --only start1-end1 start2-end2 ... into [(start1, end1), ...]. Returns None if no --only."""
    try:
        i = argv.index("--only")
    except ValueError:
        return None
    ranges = []
    for arg in argv[i + 1 :]:
        if arg.startswith("-"):
            break
        if "-" in arg:
            a, b = arg.split("-", 1)
            a, b = a.strip(), b.strip()
            if len(a) == 8 and len(b) == 8 and a.isdigit() and b.isdigit():
                ranges.append((a, b))
    return ranges if ranges else None


def build_chunks(only_ranges: list[tuple[str, str]] | None) -> list[tuple[str, str]]:
    end_year = int(os.getenv("BACKFILL_END_YEAR", datetime.now().year))
    end_month = int(os.getenv("BACKFILL_END_MONTH", datetime.now().month))
    end_day = int(os.getenv("BACKFILL_END_DAY", datetime.now().day))
    if only_ranges:
        return only_ranges
    chunks = []
    for year in range(1999, end_year + 1):
        if year < end_year:
            chunks.append((f"{year}0101", f"{year}0630"))
            chunks.append((f"{year}0701", f"{year}1231"))
        else:
            end_d = f"{end_year}{end_month:02d}{end_day:02d}"
            if end_d <= f"{year}0630":
                chunks.append((f"{year}0101", end_d))
            else:
                chunks.append((f"{year}0101", f"{year}0630"))
                chunks.append((f"{year}0701", end_d))
    return chunks


def run_backfill(lottery: str, only_ranges: list[tuple[str, str]] | None = None) -> None:
    """Run backfill for a single lottery (e.g. 'la-primitiva', 'euromillones', 'el-gordo')."""
    game_id = GAME_IDS.get(lottery)
    if not game_id:
        raise ValueError(f"Unknown lottery: {lottery}")

    chunks = build_chunks(only_ranges)
    total_chunks = len(chunks)
    end_year = int(os.getenv("BACKFILL_END_YEAR", datetime.now().year))
    end_month = int(os.getenv("BACKFILL_END_MONTH", datetime.now().month))
    end_day = int(os.getenv("BACKFILL_END_DAY", datetime.now().day))

    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    coll_name = COLLECTIONS[game_id]
    db[coll_name].create_index("id_sorteo", unique=True)

    results_path = RESULTS_PATHS.get(lottery, RESULTS_PATHS["la-primitiva"])
    results_page_url = f"{SITE_ORIGIN}{results_path}"

    if only_ranges:
        print(f"Backfill {lottery} ({game_id}) — only {total_chunks} specified range(s)")
    else:
        print(f"Backfill {lottery} ({game_id}) in 6-month chunks from 1999 to {end_year}-{end_month:02d}-{end_day:02d}")
    print(f"Total chunks: {total_chunks}")

    start_time = time.time()
    for idx, (start_d, end_d) in enumerate(chunks, 1):
        pct = int(100 * idx / total_chunks)
        elapsed = int(time.time() - start_time)
        api_url = f"{BASE_URL}?game_id={game_id}&celebrados=true&fechaInicioInclusiva={start_d}&fechaFinInclusiva={end_d}"
        try:
            data = fetch_range(api_url, results_page_url)
            saved = save_draws(db, game_id, data)
            print(f"  [{idx:3d}/{total_chunks}] {pct:3d}% ({elapsed:4d}s) {start_d}-{end_d}: {saved} draws saved")
        except Exception as e:
            print(f"  [{idx:3d}/{total_chunks}] {pct:3d}% ({elapsed:4d}s) {start_d}-{end_d}: ERROR {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS)

    elapsed_total = int(time.time() - start_time)
    last = get_max_draw_date(db, game_id)
    if last:
        set_last_draw_date(db, lottery, last)
        print(f"  Metadata: last_draw_date={last} for {lottery}")
    print(f"  {lottery} completed in {elapsed_total}s")
    client.close()
