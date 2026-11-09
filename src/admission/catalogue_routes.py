import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query


router = APIRouter(prefix="/catalogue", tags=["catalogue"])

DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "admission_ai_five_countries.sqlite"
)

Country = Literal["KR", "US", "GB", "NL", "IE"]
Degree = Literal["undergraduate", "master", "phd"]

DB_DEGREES = {
    "undergraduate": "bachelor",
    "master": "master",
    "phd": "doctoral",
}


@router.get("/programs")
def search_catalogue(
    country: Country,
    degree: Degree | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """국가와 학위로 과정 목록을 읽기 전용 조회한다."""
    db_degree = DB_DEGREES[degree] if degree is not None else None

    try:
        with closing(
            sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True)
        ) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                SELECT country_code, candidate_id, institution_name,
                       subject_label, degree, scope_group, detail_status
                FROM global_catalogue_search
                WHERE country_code = ?
                  AND (? IS NULL OR degree IN (?, ?))
                ORDER BY institution_name, subject_label, candidate_id
                LIMIT ?
                """,
                (country, db_degree, db_degree, degree, limit),
            ).fetchall()
    except sqlite3.Error:
        raise HTTPException(
            status_code=503,
            detail="과정 목록 DB를 읽을 수 없습니다.",
        ) from None

    return {"items": [dict(row) for row in rows]}