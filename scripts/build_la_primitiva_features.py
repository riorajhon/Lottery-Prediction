"""
Build La Primitiva feature/history datasets from existing MongoDB history.

Datasets:
- Per-draw feature model (`la_primitiva_draw_features`):
    - id: lottery object id (`id_sorteo`)
    - main numbers (6 per draw), complementario (C), reintegro (R)
    - draw date and weekday name
    - previous draw snapshot (id, date, weekday, numbers, C, R)
    - hot / cold for mains, complementario, reintegro (based on all previous draws only)
- Per-number history (`la_primitiva_number_history`):
    - For each main number (1-49), complementario (1-49), reintegro (0-9): list of appearances with gaps.
- Per-combination history (`la_primitiva_pair_trio_history`):
    - For each main-number pair/trio, list of appearances with gaps (main 6 only; no C/R in combos).

All features for a given draw are computed **only from earlier draws** so there
is no look-ahead.
"""

import os
import re
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from pymongo import ASCENDING, MongoClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "lottery")

# Source collection: normalized La Primitiva draws from scraper/backfill
SOURCE_COLLECTION = "la_primitiva"

# Target collection: one feature document per draw
TARGET_COLLECTION = "la_primitiva_draw_features"

# La Primitiva ranges
MAIN_MIN, MAIN_MAX = 1, 49
COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX = 1, 49  # C drawn from remaining numbers
REINTEGRO_MIN, REINTEGRO_MAX = 0, 9


@dataclass
class Draw:
    draw_id: str
    fecha_sorteo: str  # "YYYY-MM-DD" (normalized)
    main_numbers: List[int]
    complementario: Optional[int]
    reintegro: Optional[int]


def _parse_main_c_r_from_doc(doc: dict) -> Tuple[List[int], Optional[int], Optional[int]]:
    """
    Parse La Primitiva main numbers (6 from 1-49), complementario (1 from 1-49), reintegro (0-9).

    Preference:
      1. Use `numbers` (6 elements) + `complementario` + `reintegro` if present.
      2. Parse `combinacion_acta` or `combinacion` e.g. "48 - 38 - 40 - 08 - 25 - 47 C(20) R(9)".
    """
    main_numbers: List[int] = []
    complementario: Optional[int] = doc.get("complementario")
    reintegro: Optional[int] = doc.get("reintegro")

    if isinstance(doc.get("numbers"), list) and len(doc["numbers"]) >= 6:
        main_numbers = [int(n) for n in doc["numbers"][:6] if isinstance(n, (int, float))]
    else:
        text = (doc.get("combinacion_acta") or doc.get("combinacion") or "").strip()
        if isinstance(text, str) and text:
            match_c = re.search(r"C\s*\(\s*(\d+)\s*\)", text, re.I)
            match_r = re.search(r"R\s*\(\s*(\d+)\s*\)", text, re.I)
            if match_c:
                complementario = int(match_c.group(1))
            if match_r:
                reintegro = int(match_r.group(1))
            main_part = re.split(r"\s+C\s*\(|\s+R\s*\(", text)[0].strip()
            parts = re.split(r"[\s\-]+", main_part)
            for p in parts:
                p = p.strip()
                if p.isdigit():
                    main_numbers.append(int(p))
            main_numbers = main_numbers[:6]

    main_numbers = [n for n in main_numbers if MAIN_MIN <= n <= MAIN_MAX][:6]
    if complementario is not None and not (COMPLEMENTARIO_MIN <= complementario <= COMPLEMENTARIO_MAX):
        complementario = None
    if reintegro is not None and not (REINTEGRO_MIN <= reintegro <= REINTEGRO_MAX):
        reintegro = None

    return main_numbers, complementario, reintegro


def _load_draws(client: MongoClient) -> List[Draw]:
    """
    Load all La Primitiva draws sorted by fecha_sorteo ascending (oldest first).
    """
    db = client[MONGO_DB]
    col = db[SOURCE_COLLECTION]

    cursor = col.find(
        {},
        projection={
            "id_sorteo": 1,
            "fecha_sorteo": 1,
            "numbers": 1,
            "complementario": 1,
            "reintegro": 1,
            "combinacion": 1,
            "combinacion_acta": 1,
        },
    ).sort("fecha_sorteo", ASCENDING)

    draws: List[Draw] = []
    for doc in cursor:
        draw_id = str(doc.get("id_sorteo"))
        fecha_full = (doc.get("fecha_sorteo") or "").strip()
        if not draw_id or not fecha_full:
            continue
        fecha = fecha_full.split(" ")[0]
        main_numbers, complementario, reintegro = _parse_main_c_r_from_doc(doc)
        if len(main_numbers) != 6:
            continue
        draws.append(
            Draw(
                draw_id=draw_id,
                fecha_sorteo=fecha,
                main_numbers=main_numbers,
                complementario=complementario,
                reintegro=reintegro,
            )
        )

    return draws


def _weekday_name(date_str: str) -> str:
    """Return weekday name (e.g. 'Monday') for YYYY-MM-DD string."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%A")
    except Exception:
        return ""


def _build_features(draws: List[Draw]) -> None:
    """
    Build per-draw feature documents and save to TARGET_COLLECTION.
    Features for draw index i are computed using draws[0 .. i-1] only.
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    target = db[TARGET_COLLECTION]

    target.create_index([("draw_id", ASCENDING)], unique=True)

    main_freq_all: Dict[int, int] = {n: 0 for n in range(MAIN_MIN, MAIN_MAX + 1)}
    comp_freq_all: Dict[int, int] = {n: 0 for n in range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1)}
    reintegro_freq_all: Dict[int, int] = {n: 0 for n in range(REINTEGRO_MIN, REINTEGRO_MAX + 1)}

    total_draws = len(draws)
    print(f"Building per-draw features from {total_draws} La Primitiva draws...")

    for idx, draw in enumerate(draws):
        if idx > 0:
            prev = draws[idx - 1]
            prev_weekday = _weekday_name(prev.fecha_sorteo)
            prev_snapshot = {
                "prev_draw_id": prev.draw_id,
                "prev_draw_date": prev.fecha_sorteo,
                "prev_weekday": prev_weekday,
                "prev_main_numbers": prev.main_numbers,
                "prev_complementario": prev.complementario,
                "prev_reintegro": prev.reintegro,
            }
        else:
            prev_snapshot = {
                "prev_draw_id": None,
                "prev_draw_date": None,
                "prev_weekday": None,
                "prev_main_numbers": [],
                "prev_complementario": None,
                "prev_reintegro": None,
            }

        main_freq_array = [main_freq_all[n] for n in range(MAIN_MIN, MAIN_MAX + 1)]
        comp_freq_array = [comp_freq_all[n] for n in range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1)]
        reintegro_freq_array = [reintegro_freq_all[n] for n in range(REINTEGRO_MIN, REINTEGRO_MAX + 1)]

        if idx > 0:
            sorted_main = sorted(
                range(MAIN_MIN, MAIN_MAX + 1),
                key=lambda n: main_freq_all[n],
                reverse=True,
            )
            sorted_main_cold = sorted(
                range(MAIN_MIN, MAIN_MAX + 1),
                key=lambda n: main_freq_all[n],
            )
            hot_main_numbers = [n for n in sorted_main if main_freq_all[n] > 0][:6]
            cold_main_numbers = [n for n in sorted_main_cold][:6]

            sorted_comp = sorted(
                range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1),
                key=lambda n: comp_freq_all[n],
                reverse=True,
            )
            sorted_comp_cold = sorted(
                range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1),
                key=lambda n: comp_freq_all[n],
            )
            hot_complementario = [n for n in sorted_comp if comp_freq_all[n] > 0][:5]
            cold_complementario = [n for n in sorted_comp_cold][:5]

            sorted_r = sorted(
                range(REINTEGRO_MIN, REINTEGRO_MAX + 1),
                key=lambda n: reintegro_freq_all[n],
                reverse=True,
            )
            sorted_r_cold = sorted(
                range(REINTEGRO_MIN, REINTEGRO_MAX + 1),
                key=lambda n: reintegro_freq_all[n],
            )
            hot_reintegro = [n for n in sorted_r if reintegro_freq_all[n] > 0][:5]
            cold_reintegro = [n for n in sorted_r_cold][:5]
        else:
            hot_main_numbers = []
            cold_main_numbers = []
            hot_complementario = []
            cold_complementario = []
            hot_reintegro = []
            cold_reintegro = []

        weekday = _weekday_name(draw.fecha_sorteo)
        doc = {
            "draw_id": draw.draw_id,
            "draw_date": draw.fecha_sorteo,
            "weekday": weekday,
            "draw_index": idx,
            "main_numbers": draw.main_numbers,
            "complementario": draw.complementario,
            "reintegro": draw.reintegro,
            **prev_snapshot,
            "hot_main_numbers": hot_main_numbers,
            "cold_main_numbers": cold_main_numbers,
            "hot_complementario": hot_complementario,
            "cold_complementario": cold_complementario,
            "hot_reintegro": hot_reintegro,
            "cold_reintegro": cold_reintegro,
            "main_frequency_counts": main_freq_array,
            "complementario_frequency_counts": comp_freq_array,
            "reintegro_frequency_counts": reintegro_freq_array,
        }

        target.update_one(
            {"draw_id": draw.draw_id},
            {"$set": doc},
            upsert=True,
        )

        for n in draw.main_numbers:
            if MAIN_MIN <= n <= MAIN_MAX:
                main_freq_all[n] += 1
        if draw.complementario is not None and COMPLEMENTARIO_MIN <= draw.complementario <= COMPLEMENTARIO_MAX:
            comp_freq_all[draw.complementario] += 1
        if draw.reintegro is not None and REINTEGRO_MIN <= draw.reintegro <= REINTEGRO_MAX:
            reintegro_freq_all[draw.reintegro] += 1

        if (idx + 1) % 50 == 0 or idx == total_draws - 1:
            print(f"  Processed {idx + 1} / {total_draws} draws")

    client.close()
    print("Done. Per-draw features are in collection:", TARGET_COLLECTION)


def _build_number_history(draws: List[Draw]) -> None:
    """
    Build per-number appearance history for main (1-49), complementario (1-49), reintegro (0-9).

    Creates/updates collection `la_primitiva_number_history` with documents:
      { type: 'main'|'complementario'|'reintegro', number: n, appearances: [{draw_index, draw_id, date, gap_draws_since_prev}] }
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    coll = db["la_primitiva_number_history"]

    coll.create_index([("type", ASCENDING), ("number", ASCENDING)], unique=True)

    main_history: Dict[int, List[dict]] = {n: [] for n in range(MAIN_MIN, MAIN_MAX + 1)}
    comp_history: Dict[int, List[dict]] = {n: [] for n in range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1)}
    reintegro_history: Dict[int, List[dict]] = {n: [] for n in range(REINTEGRO_MIN, REINTEGRO_MAX + 1)}

    main_last_seen: Dict[int, int] = {n: -1 for n in range(MAIN_MIN, MAIN_MAX + 1)}
    comp_last_seen: Dict[int, int] = {n: -1 for n in range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1)}
    reintegro_last_seen: Dict[int, int] = {n: -1 for n in range(REINTEGRO_MIN, REINTEGRO_MAX + 1)}

    for idx, draw in enumerate(draws):
        for n in draw.main_numbers:
            if MAIN_MIN <= n <= MAIN_MAX:
                last = main_last_seen[n]
                gap = None if last == -1 else idx - last
                main_history[n].append(
                    {
                        "draw_index": idx,
                        "draw_id": draw.draw_id,
                        "date": draw.fecha_sorteo,
                        "gap_draws_since_prev": gap,
                    }
                )
                main_last_seen[n] = idx

        if draw.complementario is not None and COMPLEMENTARIO_MIN <= draw.complementario <= COMPLEMENTARIO_MAX:
            c = draw.complementario
            last = comp_last_seen[c]
            gap = None if last == -1 else idx - last
            comp_history[c].append(
                {
                    "draw_index": idx,
                    "draw_id": draw.draw_id,
                    "date": draw.fecha_sorteo,
                    "gap_draws_since_prev": gap,
                }
            )
            comp_last_seen[c] = idx

        if draw.reintegro is not None and REINTEGRO_MIN <= draw.reintegro <= REINTEGRO_MAX:
            r = draw.reintegro
            last = reintegro_last_seen[r]
            gap = None if last == -1 else idx - last
            reintegro_history[r].append(
                {
                    "draw_index": idx,
                    "draw_id": draw.draw_id,
                    "date": draw.fecha_sorteo,
                    "gap_draws_since_prev": gap,
                }
            )
            reintegro_last_seen[r] = idx

    for n in range(MAIN_MIN, MAIN_MAX + 1):
        coll.update_one(
            {"type": "main", "number": n},
            {"$set": {"type": "main", "number": n, "appearances": main_history.get(n, [])}},
            upsert=True,
        )

    for n in range(COMPLEMENTARIO_MIN, COMPLEMENTARIO_MAX + 1):
        coll.update_one(
            {"type": "complementario", "number": n},
            {"$set": {"type": "complementario", "number": n, "appearances": comp_history.get(n, [])}},
            upsert=True,
        )

    for n in range(REINTEGRO_MIN, REINTEGRO_MAX + 1):
        coll.update_one(
            {"type": "reintegro", "number": n},
            {"$set": {"type": "reintegro", "number": n, "appearances": reintegro_history.get(n, [])}},
            upsert=True,
        )

    client.close()
    print("Done. Per-number history is in collection: la_primitiva_number_history")


def _build_pair_trio_history(draws: List[Draw]) -> None:
    """
    Build per-combination appearance history for pairs/trios of main numbers only (6 choose 2, 6 choose 3).

    Creates/updates collection `la_primitiva_pair_trio_history` with documents:
      type: 'pair' or 'trio', scope: 'main', combo: [n1, n2] or [n1, n2, n3], appearances: [...]
    """
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    db.drop_collection("la_primitiva_pair_trio_history")
    coll = db["la_primitiva_pair_trio_history"]

    coll.create_index([("type", ASCENDING), ("scope", ASCENDING), ("combo", ASCENDING)])

    main_pair_history: Dict[Tuple[int, ...], List[dict]] = {}
    main_trio_history: Dict[Tuple[int, ...], List[dict]] = {}
    main_pair_last_seen: Dict[Tuple[int, int], int] = {}
    main_trio_last_seen: Dict[Tuple[int, int, int], int] = {}

    for idx, draw in enumerate(draws):
        for a, b in combinations(draw.main_numbers, 2):
            if not (MAIN_MIN <= a <= MAIN_MAX and MAIN_MIN <= b <= MAIN_MAX):
                continue
            key = tuple(sorted((a, b)))
            last = main_pair_last_seen.get(key, -1)
            gap = None if last == -1 else idx - last
            main_pair_history.setdefault(key, []).append(
                {
                    "draw_index": idx,
                    "draw_id": draw.draw_id,
                    "date": draw.fecha_sorteo,
                    "gap_draws_since_prev": gap,
                }
            )
            main_pair_last_seen[key] = idx

        for a, b, c in combinations(draw.main_numbers, 3):
            if not (
                MAIN_MIN <= a <= MAIN_MAX
                and MAIN_MIN <= b <= MAIN_MAX
                and MAIN_MIN <= c <= MAIN_MAX
            ):
                continue
            key3 = tuple(sorted((a, b, c)))
            last = main_trio_last_seen.get(key3, -1)
            gap = None if last == -1 else idx - last
            main_trio_history.setdefault(key3, []).append(
                {
                    "draw_index": idx,
                    "draw_id": draw.draw_id,
                    "date": draw.fecha_sorteo,
                    "gap_draws_since_prev": gap,
                }
            )
            main_trio_last_seen[key3] = idx

    for key, appearances in main_pair_history.items():
        coll.update_one(
            {"type": "pair", "scope": "main", "combo": list(key)},
            {
                "$set": {
                    "type": "pair",
                    "scope": "main",
                    "combo": list(key),
                    "appearances": appearances,
                }
            },
            upsert=True,
        )

    for key3, appearances in main_trio_history.items():
        coll.update_one(
            {"type": "trio", "scope": "main", "combo": list(key3)},
            {
                "$set": {
                    "type": "trio",
                    "scope": "main",
                    "combo": list(key3),
                    "appearances": appearances,
                }
            },
            upsert=True,
        )

    client.close()
    print("Done. Pair/trio history is in collection: la_primitiva_pair_trio_history")


if __name__ == "__main__":
    mongo_client = MongoClient(MONGO_URI)
    try:
        all_draws = _load_draws(mongo_client)
    finally:
        mongo_client.close()

    if not all_draws:
        print("No La Primitiva draws found. Run backfill first.")
        raise SystemExit(1)

    _build_features(all_draws)
    _build_number_history(all_draws)
    _build_pair_trio_history(all_draws)
