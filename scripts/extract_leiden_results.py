"""Extract the Leiden Ranking rows for our 5 countries from the big Results workbook.

Run on your Mac (the file is too large for Claude's workspace):

    python3 scripts/extract_leiden_results.py --inspect   # show sheets and column names
    python3 scripts/extract_leiden_results.py             # write the filtered CSV

Input : ~/Downloads/CWTS Leiden Ranking Open Edition 2026 - Results.xlsx
Output: data/raw/leiden/leiden_results_5countries.csv
Streams the workbook row by row (openpyxl read-only), so memory stays low.
"""

from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
SRC = Path.home() / "Downloads" / "CWTS Leiden Ranking Open Edition 2026 - Results.xlsx"
OUT = ROOT / "data" / "raw" / "leiden" / "leiden_results_5countries.csv"
COUNTRIES = {"South Korea", "Korea", "Republic of Korea", "United States", "United Kingdom", "Netherlands", "Ireland"}


def main() -> int:
    if not SRC.exists():
        print(f"Not found: {SRC}")
        return 1
    print("Opening workbook (this can take a minute)...")
    wb = openpyxl.load_workbook(SRC, read_only=True)
    if "--inspect" in sys.argv:
        for ws in wb.worksheets:
            rows = ws.iter_rows(values_only=True)
            print(f"\nSheet: {ws.title}")
            for i, row in enumerate(rows):
                print(row)
                if i >= 3:
                    break
        return 0
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(h) for h in next(rows)]
    country_col = next((i for i, h in enumerate(header) if h.lower() == "country"), None)
    if country_col is None:
        print("No 'Country' column. Run with --inspect and send the output.")
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    kept = total = 0
    start = time.time()
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            total += 1
            if row[country_col] in COUNTRIES:
                writer.writerow(row)
                kept += 1
            if total % 200000 == 0:
                print(f"  {total:,} rows read, {kept:,} kept ({time.time() - start:.0f}s)")
    print(f"Done: kept {kept:,} of {total:,} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
