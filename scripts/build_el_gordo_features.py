"""
Build El Gordo feature/history datasets from existing MongoDB history.

El Gordo de la Primitiva: 5 main numbers (1-54) + 1 clave (0-9).

Datasets:
- Per-draw feature model (`el_gordo_draw_features`):
    - main numbers (5 per draw), clave
    - draw date and weekday name
    - previous draw snapshot
    - hot / cold for mains and clave (based on all previous draws only)
- Per-number history (`el_gordo_number_history`):
    - For each main number (1-54), clave (0-9): list of appearances with gaps.
- Per-combination history (`el_gordo_pair_trio_history`):
    - For each main-number pair/trio only (5 choose 2, 5 choose 3).

All features for a given draw are computed **only from earlier draws** (no look-ahead).
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

SOURCE_COLLECTION = "el_gordo"
TARGET_COLLECTION = "el_gordo_draw_features"

# El Gordo: 5 main from 1-54, 1 clave from 0-9
MAIN_MIN, MAIN_MAX = 1, 54
CLAVE_MIN, CLAVE_MAX = 0, 9


@dataclass
class Draw:
    draw_id: str
    fecha_sorteo: str
    main_numbers: List[int]
    clave: Optional[int]


def _parse_main_and_clave_from_doc(doc: dict) -> Tuple[List[int], Optional[int]]:
    """
    Parse El Gordo: 5 main (1-54), 1 clave (0-9).
    Clave is stored as reintegro in API/combinacion e.g. "1-2-3-4-5 R(7)".
    """
    main_numbers: List[int] = []
    clave: Optional[int] = doc.get("reintegro")  # El Gordo uses reintegro field for clave

    if isinstance(doc.get("numbers"), list) and len(doc["numbers"]) >= 5:
        main_numbers = [int(n) for n in doc["numbers"][:5] if isinstance(n, (int, float))]
    else:
        text = (doc.get("combinacion_acta") or doc.get("combinacion") or "").strip()
        if isinstance(text, str) and text:
            match_r = re.search(r"R\s*\(\s*(\d+)\s*\)", text, re.I)
            if match_r:
                clave = int(match_r.group(1))
            main_part = re.split(r"\s+R\s*\(", text)[0].strip()
            parts = re.split(r"[\s\-]+", main_part)
            for p in parts:
                p = p.strip()
                if p.isdigit():
                    main_numbers.append(int(p))
            main_numbers = main_numbers[:5]
            # If combinacion_acta has 6 numbers, 6th is often the clave
            if clave is None and isinstance(doc.get("numbers"), list) and len(doc["numbers"]) >= 6:
                clave = int(doc["numbers"][5]) if isinstance(doc["numbers"][5], (int, float)) else None

    main_numbers = [n for n in main_numbers if MAIN_MIN <= n <= MAIN_MAX][:5]
    if clave is not None and not (CLAVE_MIN <= clave <= CLAVE_MAX):
        clave = None

    return main_numbers, clave


def _load_draws(client: MongoClient) -> List[Draw]:
    db = client[MONGO_DB]
    col = db[SOURCE_COLLECTION]

    cursor = col.find(
        {},
        projection={
            "id_sorteo": 1,
            "fecha_sorteo": 1,
            "numbers": 1,
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
        main_numbers, clave = _parse_main_and_clave_from_doc(doc)
        if len(main_numbers) != 5:
            continue
        draws.append(
            Draw(
                draw_id=draw_id,
                fecha_sorteo=fecha,
                main_numbers=main_numbers,
                clave=clave,
            )
        )

    return draws


def _weekday_name(date_str: str) -> str:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%A")
    except Exception:
        return ""


def _build_features(draws: List[Draw]) -> None:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    target = db[TARGET_COLLECTION]

    target.create_index([("draw_id", ASCENDING)], unique=True)

    main_freq_all: Dict[int, int] = {n: 0 for n in range(MAIN_MIN, MAIN_MAX + 1)}
    clave_freq_all: Dict[int, int] = {n: 0 for n in range(CLAVE_MIN, CLAVE_MAX + 1)}

    total_draws = len(draws)
    print(f"Building per-draw features from {total_draws} El Gordo draws...")

    for idx, draw in enumerate(draws):
        if idx > 0:
            prev = draws[idx - 1]
            prev_snapshot = {
                "prev_draw_id": prev.draw_id,
                "prev_draw_date": prev.fecha_sorteo,
                "prev_weekday": _weekday_name(prev.fecha_sorteo),
                "prev_main_numbers": prev.main_numbers,
                "prev_clave": prev.clave,
            }
        else:
            prev_snapshot = {
                "prev_draw_id": None,
                "prev_draw_date": None,
                "prev_weekday": None,
                "prev_main_numbers": [],
                "prev_clave": None,
            }

        main_freq_array = [main_freq_all[n] for n in range(MAIN_MIN, MAIN_MAX + 1)]
        clave_freq_array = [clave_freq_all[n] for n in range(CLAVE_MIN, CLAVE_MAX + 1)]

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
            hot_main_numbers = [n for n in sorted_main if main_freq_all[n] > 0][:5]
            cold_main_numbers = [n for n in sorted_main_cold][:5]

            sorted_clave = sorted(
                range(CLAVE_MIN, CLAVE_MAX + 1),
                key=lambda n: clave_freq_all[n],
                reverse=True,
            )
            sorted_clave_cold = sorted(
                range(CLAVE_MIN, CLAVE_MAX + 1),
                key=lambda n: clave_freq_all[n],
            )
            hot_clave = [n for n in sorted_clave if clave_freq_all[n] > 0][:5]
            cold_clave = [n for n in sorted_clave_cold][:5]
        else:
            hot_main_numbers = []
            cold_main_numbers = []
            hot_clave = []
            cold_clave = []

        weekday = _weekday_name(draw.fecha_sorteo)
        doc = {
            "draw_id": draw.draw_id,
            "draw_date": draw.fecha_sorteo,
            "weekday": weekday,
            "draw_index": idx,
            "main_numbers": draw.main_numbers,
            "clave": draw.clave,
            **prev_snapshot,
            "hot_main_numbers": hot_main_numbers,
            "cold_main_numbers": cold_main_numbers,
            "hot_clave": hot_clave,
            "cold_clave": cold_clave,
            "main_frequency_counts": main_freq_array,
            "clave_frequency_counts": clave_freq_array,
        }

        target.update_one(
            {"draw_id": draw.draw_id},
            {"$set": doc},
            upsert=True,
        )

        for n in draw.main_numbers:
            if MAIN_MIN <= n <= MAIN_MAX:
                main_freq_all[n] += 1
        if draw.clave is not None and CLAVE_MIN <= draw.clave <= CLAVE_MAX:
            clave_freq_all[draw.clave] += 1

        if (idx + 1) % 50 == 0 or idx == total_draws - 1:
            print(f"  Processed {idx + 1} / {total_draws} draws")

    client.close()
    print("Done. Per-draw features are in collection:", TARGET_COLLECTION)


def _build_number_history(draws: List[Draw]) -> None:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    coll = db["el_gordo_number_history"]

    coll.create_index([("type", ASCENDING), ("number", ASCENDING)], unique=True)

    main_history: Dict[int, List[dict]] = {n: [] for n in range(MAIN_MIN, MAIN_MAX + 1)}
    clave_history: Dict[int, List[dict]] = {n: [] for n in range(CLAVE_MIN, CLAVE_MAX + 1)}
    main_last_seen: Dict[int, int] = {n: -1 for n in range(MAIN_MIN, MAIN_MAX + 1)}
    clave_last_seen: Dict[int, int] = {n: -1 for n in range(CLAVE_MIN, CLAVE_MAX + 1)}

    for idx, draw in enumerate(draws):
        for n in draw.main_numbers:
            if MAIN_MIN <= n <= MAIN_MAX:
                last = main_last_seen[n]
                gap = None if last == -1 else idx - last
                main_history[n].append(
                    {"draw_index": idx, "draw_id": draw.draw_id, "date": draw.fecha_sorteo, "gap_draws_since_prev": gap}
                )
                main_last_seen[n] = idx

        if draw.clave is not None and CLAVE_MIN <= draw.clave <= CLAVE_MAX:
            c = draw.clave
            last = clave_last_seen[c]
            gap = None if last == -1 else idx - last
            clave_history[c].append(
                {"draw_index": idx, "draw_id": draw.draw_id, "date": draw.fecha_sorteo, "gap_draws_since_prev": gap}
            )
            clave_last_seen[c] = idx

    for n in range(MAIN_MIN, MAIN_MAX + 1):
        coll.update_one(
            {"type": "main", "number": n},
            {"$set": {"type": "main", "number": n, "appearances": main_history.get(n, [])}},
            upsert=True,
        )

    for n in range(CLAVE_MIN, CLAVE_MAX + 1):
        coll.update_one(
            {"type": "clave", "number": n},
            {"$set": {"type": "clave", "number": n, "appearances": clave_history.get(n, [])}},
            upsert=True,
        )

    client.close()
    print("Done. Per-number history is in collection: el_gordo_number_history")


def _build_pair_trio_history(draws: List[Draw]) -> None:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]

    db.drop_collection("el_gordo_pair_trio_history")
    coll = db["el_gordo_pair_trio_history"]

    coll.create_index([("type", ASCENDING), ("scope", ASCENDING), ("combo", ASCENDING)])

    main_pair_history: Dict[Tuple[int, int], List[dict]] = {}
    main_trio_history: Dict[Tuple[int, int, int], List[dict]] = {}
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
                {"draw_index": idx, "draw_id": draw.draw_id, "date": draw.fecha_sorteo, "gap_draws_since_prev": gap}
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
                {"draw_index": idx, "draw_id": draw.draw_id, "date": draw.fecha_sorteo, "gap_draws_since_prev": gap}
            )
            main_trio_last_seen[key3] = idx

    for key, appearances in main_pair_history.items():
        coll.update_one(
            {"type": "pair", "scope": "main", "combo": list(key)},
            {"$set": {"type": "pair", "scope": "main", "combo": list(key), "appearances": appearances}},
            upsert=True,
        )

    for key3, appearances in main_trio_history.items():
        coll.update_one(
            {"type": "trio", "scope": "main", "combo": list(key3)},
            {"$set": {"type": "trio", "scope": "main", "combo": list(key3), "appearances": appearances}},
            upsert=True,
        )

    client.close()
    print("Done. Pair/trio history is in collection: el_gordo_pair_trio_history")


def main() -> None:
    """Rebuild El Gordo features, number history and pair/trio history from all draws."""
    mongo_client = MongoClient(MONGO_URI)
    try:
        all_draws = _load_draws(mongo_client)
    finally:
        mongo_client.close()

    if not all_draws:
        print("No El Gordo draws found. Run backfill first.")
        return

    _build_features(all_draws)
    _build_number_history(all_draws)
    _build_pair_trio_history(all_draws)


if __name__ == "__main__":
    main()
