"""Branchekoder (Dansk Branchekode DB25, Danmarks Statistik) – opslag, søgning og hierarki.

Data: integrations/data/db25.json (bygges af data/build_db25.py). En virksomhed
registreres i CVR på niveau 5 (6 cifre, fx 692000 = 69.20.00).
"""

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).parent / "data" / "db25.json"


@lru_cache(maxsize=1)
def _data():
    return json.loads(DATA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _index():
    by_code, codes = {}, []
    for item in _data()["items"]:
        by_code[item["code"]] = item
        if item["level"] == 5:
            codes.append(item)
    return by_code, codes


def _norm(text):
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def normalize_code(code):
    """'69.20.00' / '692000' / DB07-kode → (DB25-kode på 6 cifre, converted_from_db07) eller (None, False)."""
    digits = re.sub(r"\D", "", str(code or ""))
    by_code, _ = _index()
    if len(digits) == 6 and digits in by_code:
        return digits, False
    mapped = _data()["db07_to_db25"].get(digits)
    if mapped and mapped in by_code:
        return mapped, True
    return None, False


def describe(code):
    """Kodens titel og overordnede niveauer (til visning), eller None."""
    norm, converted = normalize_code(code)
    if not norm:
        return None
    by_code, _ = _index()
    item = by_code[norm]
    return {**_public(item), "path": _path(item), "includes": item["includes"], "excludes": item["excludes"],
            "converted_from_db07": str(code) if converted else None}


def _public(item):
    return {"code": item["code"], "display": item["display"], "title": item["title"], "level": item["level"],
            "section": item["section"]}


def _path(item):
    """Hovedafdeling → hovedgruppe → gruppe → undergruppe for en kode på niveau 5."""
    by_code, _ = _index()
    d = item["display"]  # 69.20.00
    parents = [item["section"], d[:2], d[:4], d[:5]]
    out = []
    for p in parents:
        parent = by_code.get(p.replace(".", ""))
        if parent and parent["code"] != item["code"] and parent["title"] not in [x["title"] for x in out]:
            out.append({"display": parent["display"], "title": parent["title"]})
    return out


def search(query, limit=25):
    """Søg i koder, titler og beskrivelser. Kode-præfiks og titel rangeres før beskrivelse."""
    _, codes = _index()
    q = _norm(query)
    if not q:
        return []
    digits = re.sub(r"[\s.]", "", q)
    words = q.split()
    scored = []
    for item in codes:
        title = _norm(item["title"])
        score = 0
        if digits.isdigit():
            if item["code"].startswith(digits):
                score = 100 - len(item["code"])
        else:
            if all(w in title for w in words):
                score = 80 if title.startswith(words[0]) else 60
            elif all(w in title + " " + _norm(item["includes"]) for w in words):
                score = 30
        if score:
            scored.append((-score, item["display"], item))
    scored.sort(key=lambda t: (t[0], t[1]))
    return [{**_public(i), "hint": _hint(i, words)} for _, _, i in scored[:limit]]


def _hint(item, words):
    """Kort uddrag af beskrivelsen, der forklarer, hvorfor koden matcher."""
    text = item["includes"]
    low = _norm(text)
    for w in words:
        pos = low.find(w)
        if pos >= 0 and w not in _norm(item["title"]):
            start = max(0, pos - 40)
            return ("…" if start else "") + text[start:pos + 80].strip() + "…"
    return ""


def tree():
    """Hele hierarkiet til oversigten: hovedafdelinger med koder på niveau 2 og 5."""
    sections, current, group = [], None, None
    for item in _data()["items"]:
        if item["level"] == 1:
            current = {**_public(item), "groups": []}
            sections.append(current)
        elif item["level"] == 2 and current is not None:
            group = {**_public(item), "codes": []}
            current["groups"].append(group)
        elif item["level"] == 5 and group is not None:
            group["codes"].append(_public(item))
    return {"version": _data()["version"], "sections": sections}
