"""Byg integrations/data/db25.json ud fra Danmarks Statistiks filer.

Kilder (hentet 2026-11-15 fra dst.dk/da/Statistik/dokumentation/nomenklaturer/db):
  source/db25.csv            Dansk Branchekode 2025 (DB25) V1:2025-, alle niveauer (CSV, dansk)
  source/db07_til_db25.xlsx  Nøgle DB07 -> DB25 (FRA_KODE, TIL_KODE, antal_vaegt, ...)

CVR har brugt DB25 siden 1. januar 2025. Ældre DB07-koder oversættes til den
DB25-kode, de fleste virksomheder (antal_vaegt) flyttede til.

Opdatering: hent de nye filer, læg dem i source/ og kør
    .venv/bin/python integrations/data/build_db25.py
"""

import csv
import json
import re
from pathlib import Path

import openpyxl

HERE = Path(__file__).parent


def clean(text):
    text = re.sub(r"\s+", " ", (text or "").replace("- ", " ")).strip()
    return text


def main():
    rows = list(csv.DictReader(open(HERE / "source/db25.csv", encoding="utf-8-sig"), delimiter=";"))
    items, section = [], ""
    for r in rows:
        level = int(r["NIVEAU"])
        code = r["KODE"].strip()
        if level == 1:
            section = code
        items.append({
            "code": code.replace(".", ""),       # som i CVR: 692000
            "display": code,                      # 69.20.00
            "level": level,                       # 1 hovedafdeling … 5 dansk underbranche
            "section": section,
            "title": r["TITEL"].strip(),
            "includes": clean(" ".join([r["GENERELLE_NOTER"], r["INKLUDERER"], r["INKLUDERER_OGSÅ"]])),
            "excludes": clean(r["EKSKLUDERER"]),
        })

    best = {}
    wb = openpyxl.load_workbook(HERE / "source/db07_til_db25.xlsx", read_only=True)
    for i, (src, dst, weight, *_rest) in enumerate(wb.worksheets[0].iter_rows(values_only=True)):
        if i == 0 or not src:
            continue
        if src not in best or (weight or 0) > best[src][1]:
            best[src] = (dst, weight or 0)

    out = {"version": "DB25 V1:2025-", "source": "Danmarks Statistik", "items": items,
           "db07_to_db25": {k: v[0] for k, v in sorted(best.items())}}
    (HERE / "db25.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(items)} koder, {len(best)} DB07-nøgler")


if __name__ == "__main__":
    main()
