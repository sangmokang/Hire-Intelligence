from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.candidate_profiler import CandidateProfilerRequest, CandidateProfilerResponse
from app.services.candidate_profiler_service import CandidateProfilerService

router = APIRouter(prefix="/candidate-profiler", tags=["candidate-profiler"])


@router.post("", response_model=ApiResponse[CandidateProfilerResponse])
def analyze_candidate(
    request: CandidateProfilerRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[CandidateProfilerResponse]:
    """후보자 TDS 분석 — 학력·경력·스킬 기반 인재 밀도 점수 산출"""
    # 입력 검증: 최소 하나의 정보 필요
    if not request.resume_text and not request.current_company and not request.skills:
        raise HTTPException(status_code=400, detail="입력 정보가 부족합니다.")

    service = CandidateProfilerService(db)
    result = service.analyze(request)
    return ApiResponse(data=result)
