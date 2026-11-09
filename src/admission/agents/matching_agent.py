from pathlib import Path

from admission.program_repository import load_programs
from admission.recommend import recommend
from admission.schemas import RequestContext
from admission.official_sources import load_allowed_hosts


def run_matching_agent(
    context: RequestContext,
    use_integrated_data: bool = False,
) -> dict:
    """
    사용자 조건에 맞는 대학 프로그램을 검색한다.

    기본값: 기존 검증 데이터 사용
    선택값: 통합된 93개 프로그램 데이터 사용
    """

    if use_integrated_data:
        project_root = Path(__file__).resolve().parents[3]
        data_path = project_root / "data" / "programs_integrated.json"
        programs = load_programs(data_path)
    else:
        programs = load_programs()

    result = recommend(
        context,
        programs=programs,
        allowed_hosts=load_allowed_hosts(),
    )

    return {
        "stage": "matching",
        "dataSource": (
            "integrated"
            if use_integrated_data
            else "verified_dataset"
        ),
        "recommendation": result,
    }