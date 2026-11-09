from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from admission.program_filter import filter_programs
from admission.program_repository import load_programs
from admission.program_schemas import Program
from admission.schemas import RequestContext
from admission.scope import check_scope


router = APIRouter(prefix="/programs", tags=["programs"])


class CandidateResponse(BaseModel):
    candidates: list[Program]
    count: int
    message: str


@router.post("/candidates", response_model=CandidateResponse)
def get_candidates(context: RequestContext):
    scope_notices = check_scope(context)

    if scope_notices:
        raise HTTPException(
            status_code=422,
            detail={"scopeNotices": scope_notices},
        )

    candidates = filter_programs(load_programs(), context)

    return CandidateResponse(
        candidates=candidates,
        count=len(candidates),
        message=(
            "현재 저장된 데이터에서 찾은 후보입니다. "
            "입학 자격과 정보의 최신성 검증은 아직 수행하지 않았습니다."
        ),
    )