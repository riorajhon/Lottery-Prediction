"""
Lottery Prediction API — scrape lottery draws and save to MongoDB.
Uses Selenium with a new Chrome instance (pattern from refer.py).
Three collections: la_primitiva, euromillones, el_gordo.
Stores combinacion (main), parsed numbers/C/R, and joker combinacion.
"""
import json
import logging
import os
import re
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from datetime import datetime as dt

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Lottery slug -> game_id for loteriasyapuestas.es API (El Gordo = ELGR per site)
GAME_IDS = {
    "la-primitiva": "LAPR",
    "euromillones": "EMIL",
    "el-gordo": "ELGR",
}

# Results page path per lottery (load this first so real Chrome has correct referer/cookies)
RESULTS_PATHS = {
    "la-primitiva": "/es/resultados/la-primitiva",
    "euromillones": "/es/resultados/euromillones",
    "el-gordo": "/es/resultados/gordo-primitiva",
}

# Daily scrape at 00:02 and Update button: process in this order
LOTTERY_DAILY_ORDER = ["euromillones", "la-primitiva", "el-gordo"]

BASE_URL = "https://www.loteriasyapuestas.es/servicios/buscadorSorteos"
SITE_ORIGIN = "https://www.loteriasyapuestas.es"

# One collection per lottery (El Gordo = ELGR)
COLLECTIONS = {"LAPR": "la_primitiva", "EMIL": "euromillones", "ELGR": "el_gordo"}
METADATA_COLLECTION = "scraper_metadata"

logger = logging.getLogger("lottery")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "lottery")

client: MongoClient | None = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, db
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    for coll_name in COLLECTIONS.values():
        db[coll_name].create_index("id_sorteo", unique=True)
    yield
    if client:
        client.close()


def parse_combinacion(combinacion: str) -> dict:
    """
    Parse "04 - 12 - 16 - 37 - 39 - 45 C(44) R(9)" into numbers array, C, R.
    """
    numbers = []
    complementario = None
    reintegro = None
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
    """Add parsed numbers, C, R, and joker_combinacion; keep all original fields."""
    out = dict(draw)
    combinacion = draw.get("combinacion") or ""
    parsed = parse_combinacion(combinacion)
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


app = FastAPI(title="Lottery Prediction API", lifespan=lifespan)

# Allow frontend on common dev ports (5173 = default Vite, 5174+ when 5173 is in use)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://151.241.216.178:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def create_driver() -> webdriver.Chrome:
    """
    Create a new Chrome browser via Selenium (same pattern as refer.py).
    Headless on all platforms for API use; Linux gets extra stability flags.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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


def _scrape_with_selenium(api_url: str, results_page_url: str) -> list:
    """Launch a new Chrome via Selenium, load results page, fetch API URL, return JSON list."""
    driver = None
    try:
        driver = create_driver()
        driver.get(results_page_url)
        data = driver.execute_async_script(
            """
            var url = arguments[0];
            var callback = arguments[arguments.length - 1];
            fetch(url)
                .then(function(r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
                .then(callback)
                .catch(function(e) { callback({__error: e.message}); });
            """,
            api_url,
        )
        if isinstance(data, dict) and data.get("__error"):
            raise RuntimeError(data["__error"])
        return data
    except Exception:
        raise
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning("Driver quit failed (ignored): %s", e)


@app.get("/api/scrape")
def scrape(
    start_date: str = Query(..., description="YYYYMMDD"),
    end_date: str = Query(..., description="YYYYMMDD"),
    lottery: str = Query(..., description="la-primitiva | euromillones | el-gordo"),
):
    """Fetch draws from loteriasyapuestas.es using Selenium Chrome, save to MongoDB."""
    game_id = GAME_IDS.get(lottery)
    if not game_id:
        raise HTTPException(400, detail=f"Unknown lottery: {lottery}")

    api_url = (
        f"{BASE_URL}"
        f"?game_id={game_id}"
        "&celebrados=true"
        f"&fechaInicioInclusiva={start_date}"
        f"&fechaFinInclusiva={end_date}"
    )
    results_path = RESULTS_PATHS.get(lottery, RESULTS_PATHS["la-primitiva"])
    results_page_url = f"{SITE_ORIGIN}{results_path}"

    try:
        data = _scrape_with_selenium(api_url, results_page_url)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Selenium scrape error")
        raise HTTPException(502, detail=f"Chrome scrape failed: {e!s}")

    if not isinstance(data, list):
        got = type(data).__name__
        if isinstance(data, dict):
            got = f"dict keys: {list(data.keys())[:10]}"
        raise HTTPException(
            502,
            detail=f"API did not return a list of draws (got {got})",
        )

    saved, errors = _save_draws_to_db(data)
    max_date = _max_date_from_draws(data)
    if max_date:
        _set_last_draw_date(lottery, max_date)

    return {
        "saved": saved,
        "total": len(data),
        "lottery": lottery,
        "game_id": game_id,
        "start_date": start_date,
        "end_date": end_date,
        "message": f"Saved {saved} draws to MongoDB.",
        "errors": errors[:5] if errors else None,
    }


def _get_last_draw_date(lottery: str) -> str | None:
    """Get last_draw_date for a lottery from scraper_metadata."""
    if db is None:
        return None
    doc = db[METADATA_COLLECTION].find_one({"lottery": lottery}, projection=["last_draw_date"])
    return (doc.get("last_draw_date") or "").strip() or None


def _set_last_draw_date(lottery: str, date_str: str) -> None:
    """Set last_draw_date for a lottery in scraper_metadata."""
    if db is None:
        return
    db[METADATA_COLLECTION].update_one(
        {"lottery": lottery},
        {"$set": {"last_draw_date": date_str}},
        upsert=True,
    )


def _max_date_from_draws(data: list) -> str | None:
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


def _save_draws_to_db(data: list) -> tuple[int, list]:
    """Upsert draws into the correct collection (la_primitiva / euromillones / el_gordo)."""
    if db is None:
        raise HTTPException(500, detail="Database not connected")
    saved = 0
    errors = []
    for draw in data:
        if not isinstance(draw, dict):
            continue
        draw_id = draw.get("id_sorteo")
        game_id = draw.get("game_id")
        if not draw_id or not game_id:
            continue
        coll_name = COLLECTIONS.get(game_id)
        if not coll_name:
            continue
        try:
            doc = normalize_draw(draw)
            db[coll_name].replace_one(
                {"id_sorteo": draw_id},
                doc,
                upsert=True,
            )
            saved += 1
        except PyMongoError as e:
            errors.append(str(e))
    return saved, errors


# game_id -> display name for API responses
GAME_ID_TO_NAME = {"LAPR": "La Primitiva", "EMIL": "Euromillones", "ELGR": "El Gordo"}


def _doc_to_json(doc: dict) -> dict:
    """Convert a MongoDB document to a JSON-serializable dict (all keys from DB)."""
    out = {}
    for k, v in doc.items():
        if k == "_id":
            out[k] = str(v) if isinstance(v, ObjectId) else v
        elif isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, dt):
            out[k] = v.isoformat() if hasattr(v, "isoformat") else str(v)
        elif isinstance(v, list):
            out[k] = [_item_to_json(x) for x in v]
        elif isinstance(v, dict):
            out[k] = _doc_to_json(v)
        else:
            out[k] = v
    return out


def _item_to_json(x):
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, dt):
        return x.isoformat() if hasattr(x, "isoformat") else str(x)
    if isinstance(x, dict):
        return _doc_to_json(x)
    if isinstance(x, list):
        return [_item_to_json(i) for i in x]
    return x


# Keys we send to frontend; we always set these from the raw doc so combinacion_acta and escrutinio are never missing
DRAW_KEYS = (
    "id_sorteo",
    "fecha_sorteo",
    "game_id",
    "combinacion",
    "combinacion_acta",
    "numbers",
    "complementario",
    "reintegro",
    "joker_combinacion",
    "premio_bote",
    "escrutinio",
    # Euromillones extra stats (if present in DB)
    "apuestas",  # bets received
    "aquestas",  # fallback name if mis-typed in DB
    "recaudacion",
    "recaudacion_europea",
    "premios",
    "escrutinio_millon",
)


def _build_draw(doc: dict, game_id: str) -> dict:
    """Build one draw for API: always include combinacion_acta and escrutinio from doc."""
    draw = {}
    for k in DRAW_KEYS:
        v = doc.get(k)
        draw[k] = _item_to_json(v) if v is not None else None
    draw["game_name"] = GAME_ID_TO_NAME.get(game_id, game_id)
    if draw.get("joker_combinacion") is None:
        millon = doc.get("millon") or {}
        draw["joker_combinacion"] = millon.get("combinacion") if isinstance(millon, dict) else None
    return draw


@app.get("/api/draws")
def get_draws(
    lottery: str = Query(None, description="la-primitiva | euromillones | el-gordo"),
    from_date: str = Query(None, description="YYYY-MM-DD"),
    to_date: str = Query(None, description="YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """Fetch draws: use find() then build each draw in Python so combinacion_acta and escrutinio are always returned."""
    if db is None:
        raise HTTPException(500, detail="Database not connected")
    query = {}
    if from_date or to_date:
        query["fecha_sorteo"] = {}
        if from_date:
            query["fecha_sorteo"]["$gte"] = from_date + " 00:00:00"
        if to_date:
            query["fecha_sorteo"]["$lte"] = to_date + " 23:59:59"

    if lottery and lottery in GAME_IDS:
        coll_name = COLLECTIONS.get(GAME_IDS[lottery])
        collections_to_query = [(coll_name, GAME_IDS[lottery])] if coll_name else []
    else:
        collections_to_query = [(name, gid) for gid, name in COLLECTIONS.items()]

    all_draws = []
    total = 0
    one_lottery = len(collections_to_query) == 1

    for coll_name, game_id in collections_to_query:
        cursor = db[coll_name].find(query).sort("fecha_sorteo", -1)
        if one_lottery:
            total = db[coll_name].count_documents(query)
            for doc in cursor.skip(skip).limit(limit):
                all_draws.append(_build_draw(doc, game_id))
        else:
            for doc in cursor:
                total += 1
                all_draws.append(_build_draw(doc, game_id))

    if not one_lottery:
        all_draws.sort(key=lambda d: d.get("fecha_sorteo") or "", reverse=True)
        total = len(all_draws)
        all_draws = all_draws[skip : skip + limit]

    return JSONResponse(content={"draws": all_draws, "total": total})


@app.get("/api/debug/euromillones-one")
def debug_euromillones_one():
    """Return one raw document from euromillones to verify combinacion_acta and escrutinio."""
    if db is None:
        raise HTTPException(500, detail="Database not connected")
    doc = db["euromillones"].find_one(sort=[("fecha_sorteo", -1)])
    if not doc:
        return JSONResponse(content={"error": "No document in euromillones"})
    return JSONResponse(content=_doc_to_json(doc))


@app.get("/api/euromillones/features")
def get_euromillones_features(
    limit: int = Query(50, ge=1, le=200),
    skip: int = Query(0, ge=0),
):
    """
    Return per-draw Euromillones feature rows from `euromillones_draw_features`.

    Each document contains:
      - main_numbers, star_numbers
      - draw_date, weekday
      - hot/cold numbers
      - frequency and gap arrays
      - previous-draw snapshot fields
    """
    if db is None:
        raise HTTPException(500, detail="Database not connected")

    coll = db["euromillones_draw_features"]
    total = coll.count_documents({})

    cursor = coll.find().sort("draw_date", -1).skip(skip).limit(limit)
    docs = [_doc_to_json(doc) for doc in cursor]

    return JSONResponse(content={"features": docs, "total": total})


@app.get("/api/euromillones/gaps")
def get_euromillones_gaps(
    type: str = Query("main", pattern="^(main|star)$"),
    end_date: str | None = Query(
        None,
        description="YYYY-MM-DD. If not provided, uses today.",
    ),
    window_days: int = Query(
        31,
        ge=1,
        le=365,
        description="Number of days to include ending at end_date.",
    ),
):
    """
    Return per-number appearance history for Euromillones.

    Response format:
      {
        "points": [
          { "type": "main", "number": 3, "draw_index": 12, "date": "2026-01-24" },
          ...
        ]
      }
    """
    if db is None:
        raise HTTPException(500, detail="Database not connected")

    from datetime import datetime, timedelta

    coll = db["euromillones_number_history"]
    docs = list(coll.find({"type": type}))

    points: list[dict] = []

    # Determine time window
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(400, detail="Invalid end_date format, expected YYYY-MM-DD")
    else:
        end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=window_days)

    for doc in docs:
        number = doc.get("number")
        appearances = doc.get("appearances") or []
        for appo in appearances:
            date_str = (appo.get("date") or "").split(" ")[0]
            if not date_str:
                continue
            try:
                app_dt = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            if not (start_dt <= app_dt <= end_dt):
                continue
            points.append(
                {
                    "type": type,
                    "number": number,
                    "draw_index": appo.get("draw_index"),
                    "date": date_str,
                }
            )

    # Sort points by date ascending so charts have ordered Y-axis
    points.sort(key=lambda p: p.get("date") or "")

    return JSONResponse(content={"points": points})


@app.get("/api/euromillones/apuestas")
def get_euromillones_apuestas(
    window: str = Query(
        "3m",
        pattern="^(3m|6m|1y|all)$",
        description="Time window: last 3m, 6m, 1y or all history.",
    ),
):
    """
    Time series for Euromillones apuestas / premios / premio_bote.

    Returns draws ordered ascending by fecha_sorteo. Each point:
      {
        "draw_id": "...",
        "date": "YYYY-MM-DD",
        "apuestas": int | null,
        "premios": float | null,
        "premio_bote": float | null
      }
    """
    if db is None:
        raise HTTPException(500, detail="Database not connected")

    from datetime import datetime, timedelta

    coll = db["euromillones"]

    # Determine date window
    if window == "all":
        query: dict = {}
    else:
        today = datetime.utcnow().date()
        if window == "3m":
            delta_days = 90
        elif window == "6m":
            delta_days = 180
        else:  # "1y"
            delta_days = 365
        start_date = today - timedelta(days=delta_days)
        query = {
            "fecha_sorteo": {
                "$gte": start_date.strftime("%Y-%m-%d") + " 00:00:00",
                "$lte": today.strftime("%Y-%m-%d") + " 23:59:59",
            }
        }

    cursor = coll.find(
        query,
        projection={
            "id_sorteo": 1,
            "fecha_sorteo": 1,
            "apuestas": 1,
            "aquestas": 1,
            "premio_bote": 1,
            "premios": 1,
        },
    ).sort("fecha_sorteo", 1)

    points: list[dict] = []
    for doc in cursor:
        draw_id = str(doc.get("id_sorteo"))
        fecha_full = (doc.get("fecha_sorteo") or "").strip()
        if not draw_id or not fecha_full:
            continue
        date = fecha_full.split(" ")[0]

        raw_apuestas = doc.get("apuestas")
        if raw_apuestas in (None, ""):
            raw_apuestas = doc.get("aquestas")
        try:
            apuestas = int(str(raw_apuestas).replace(".", "").replace(",", "")) if raw_apuestas not in (None, "") else None
        except Exception:
            apuestas = None

        def _to_float(val):
            if val in (None, ""):
                return None
            try:
                s = str(val).replace(".", "").replace(",", ".")
                return float(s)
            except Exception:
                return None

        premios = _to_float(doc.get("premios"))
        if premios is not None:
            # Valores de premios vienen 100x; normalizar a euros reales
            premios = premios / 100.0
        premio_bote = _to_float(doc.get("premio_bote"))

        points.append(
            {
                "draw_id": draw_id,
                "date": date,
                "apuestas": apuestas,
                "premios": premios,
                "premio_bote": premio_bote,
            }
        )

    return JSONResponse(content={"points": points})


def _apuestas_time_series_for_lottery(lottery_slug: str, window: str):
    """
    Helper to build apuestas / premios / premio_bote time series for a given lottery.
    lottery_slug: 'la-primitiva' | 'el-gordo'
    """
    if db is None:
        raise HTTPException(500, detail="Database not connected")

    from datetime import datetime, timedelta

    game_id = GAME_IDS.get(lottery_slug)
    if not game_id:
        raise HTTPException(400, detail=f"Unknown lottery: {lottery_slug}")
    coll_name = COLLECTIONS.get(game_id)
    if not coll_name:
        raise HTTPException(400, detail=f"No collection for lottery: {lottery_slug}")

    coll = db[coll_name]

    # Determine date window
    if window == "all":
        query: dict = {}
    else:
        today = datetime.utcnow().date()
        if window == "3m":
            delta_days = 90
        elif window == "6m":
            delta_days = 180
        else:  # "1y"
            delta_days = 365
        start_date = today - timedelta(days=delta_days)
        query = {
            "fecha_sorteo": {
                "$gte": start_date.strftime("%Y-%m-%d") + " 00:00:00",
                "$lte": today.strftime("%Y-%m-%d") + " 23:59:59",
            }
        }

    cursor = coll.find(
        query,
        projection={
            "id_sorteo": 1,
            "fecha_sorteo": 1,
            "apuestas": 1,
            "recaudacion": 1,
            "premio_bote": 1,
            "premios": 1,
        },
    ).sort("fecha_sorteo", 1)

    def _to_float(val):
        if val in (None, ""):
            return None
        try:
            s = str(val).replace(".", "").replace(",", ".")
            return float(s)
        except Exception:
            return None

    points: list[dict] = []
    for doc in cursor:
        draw_id = str(doc.get("id_sorteo"))
        fecha_full = (doc.get("fecha_sorteo") or "").strip()
        if not draw_id or not fecha_full:
            continue
        date = fecha_full.split(" ")[0]

        raw_apuestas = doc.get("apuestas")
        try:
            apuestas = int(str(raw_apuestas).replace(".", "").replace(",", "")) if raw_apuestas not in (None, "") else None
        except Exception:
            apuestas = None

        premios = _to_float(doc.get("premios"))
        if premios is not None:
            premios = premios / 100.0
        premio_bote = _to_float(doc.get("premio_bote"))

        points.append(
            {
                "draw_id": draw_id,
                "date": date,
                "apuestas": apuestas,
                "premios": premios,
                "premio_bote": premio_bote,
            }
        )

    return points


@app.get("/api/la-primitiva/apuestas")
def get_la_primitiva_apuestas(
    window: str = Query(
        "3m",
        pattern="^(3m|6m|1y|all)$",
        description="Time window: last 3m, 6m, 1y or all history.",
    ),
):
    points = _apuestas_time_series_for_lottery("la-primitiva", window)
    return JSONResponse(content={"points": points})


@app.get("/api/el-gordo/apuestas")
def get_el_gordo_apuestas(
    window: str = Query(
        "3m",
        pattern="^(3m|6m|1y|all)$",
        description="Time window: last 3m, 6m, 1y or all history.",
    ),
):
    points = _apuestas_time_series_for_lottery("el-gordo", window)
    return JSONResponse(content={"points": points})

@app.get("/api/euromillones/number-history")
def get_euromillones_number_history():
    """
    Return full per-number appearance history for Euromillones, grouped by type.

    Response format:
      {
        "main": [
          { "number": 1, "dates": ["2026-01-13", "2026-01-27", ...] },
          ...
        ],
        "star": [
          { "number": 1, "dates": ["2026-01-20", ...] },
          ...
        ]
      }
    """
    if db is None:
        raise HTTPException(500, detail="Database not connected")

    coll = db["euromillones_number_history"]

    docs = list(
        coll.find(
            {},
            projection={
                "_id": 0,
                "type": 1,
                "number": 1,
                "appearances.date": 1,
            },
        )
    )

    main: list[dict] = []
    star: list[dict] = []

    for doc in docs:
        t = doc.get("type")
        number = doc.get("number")
        appearances = doc.get("appearances") or []

        dates_set: set[str] = set()
        for appo in appearances:
            date_str = (appo.get("date") or "").split(" ")[0]
            if date_str:
                dates_set.add(date_str)

        dates = sorted(dates_set)

        target = main if t == "main" else star if t == "star" else None
        if target is not None:
            target.append({"number": number, "dates": dates})

    return JSONResponse(content={"main": main, "star": star})


@app.post("/api/scrape/daily")
def scrape_daily():
    """
    Daily scrape for all lotteries: from (today - 3 days) to today.
    Call at 00:02 via scheduler or manually. Saves/updates draws; updates last_draw_date.
    """
    from datetime import datetime, timedelta
    if db is None:
        raise HTTPException(500, detail="Database not connected")
    today = datetime.now().strftime("%Y-%m-%d")
    today_yyyymmdd = today.replace("-", "")
    from_d = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    start_yyyymmdd = from_d.replace("-", "")
    results = []
    for lottery in LOTTERY_DAILY_ORDER:
        game_id = GAME_IDS[lottery]
        api_url = (
            f"{BASE_URL}?game_id={game_id}&celebrados=true"
            f"&fechaInicioInclusiva={start_yyyymmdd}&fechaFinInclusiva={today_yyyymmdd}"
        )
        results_path = RESULTS_PATHS.get(lottery, RESULTS_PATHS["la-primitiva"])
        results_page_url = f"{SITE_ORIGIN}{results_path}"
        try:
            data = _scrape_with_selenium(api_url, results_page_url)
            if not isinstance(data, list):
                results.append({"lottery": lottery, "saved": 0, "message": "Invalid response"})
                continue
            saved, _ = _save_draws_to_db(data)
            max_date = _max_date_from_draws(data)
            if max_date:
                _set_last_draw_date(lottery, max_date)
            results.append({"lottery": lottery, "saved": saved, "message": f"Saved {saved} draws"})
        except Exception as e:
            results.append({"lottery": lottery, "saved": 0, "message": str(e)})
    return {"results": results, "date": today}


@app.post("/api/scrape/import")
async def scrape_import(body: list):
    """
    Save draws from pasted JSON (e.g. when the lottery API returns 403).
    Open the buscadorSorteos URL in your browser, copy the JSON array, paste here.
    """
    if not isinstance(body, list):
        raise HTTPException(400, detail="Body must be a JSON array of draws")
    saved, errors = _save_draws_to_db(body)
    return {
        "saved": saved,
        "total": len(body),
        "message": f"Saved {saved} draws to MongoDB.",
        "errors": errors[:5] if errors else None,
    }
