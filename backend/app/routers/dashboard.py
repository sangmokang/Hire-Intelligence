from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.middleware.plan_access import require_pro
from app.models.pulse import WeeklySnapshot
from app.schemas.common import ApiResponse
from app.schemas.dashboard import (
    ResumeMatchRequest,
    ResumeMatchOutput,
    MatchResult,
    SDMatrixResponse,
    DashboardSummary,
    SegmentData,
    CompanyRankItem,
    CompanyTimeline,
    TimelineDataPoint,
    SegmentTrend,
    TrendDataPoint,
    CompanyProfile,
    TalentDensity,
    HiringPower,
    DashboardMetadata,
)
from app.services.dashboard_service import DashboardService
from app.services.jd_insights_service import JdInsightsService
from app.schemas.jd_analysis import JdInsightsResponse
from app.schemas.company_dna import CompanyDnaResponse, SegmentBenchmarkResponse, DnaComparisonResponse, DnaTrendResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metadata", response_model=ApiResponse[DashboardMetadata])
def get_dashboard_metadata(
    db: Session = Depends(get_db),
):
    """대시보드 메타데이터 — 최신 데이터 기준 주차 및 갱신 시각 (인증 불필요)"""
    row = (
        db.query(
            func.max(WeeklySnapshot.week).label("latest_week"),
            func.max(WeeklySnapshot.created_at).label("updated_at"),
        )
        .first()
    )
    if row is None or row.latest_week is None:
        return ApiResponse(data=DashboardMetadata())

    return ApiResponse(
        data=DashboardMetadata(
            latest_week=row.latest_week,
            updated_at=row.updated_at,
        )
    )


def _compute_quadrant(sd_ratio: float) -> str:
    """SD ratio를 기반으로 quadrant 계산"""
    if sd_ratio >= 1.3:
        return "OPPORTUNITY"
    elif sd_ratio >= 1.0:
        return "COMPETITIVE"
    elif sd_ratio >= 0.8:
        return "NICHE"
    else:
        return "OVERSUPPLY"


@router.get("/sd-matrix", response_model=ApiResponse[SDMatrixResponse])
def get_sd_matrix(
    week: str | None = Query(None, description="ISO 주차 (예: 2024-W01)"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """수급 매트릭스 - 전체 직군별 수요/공급 현황"""
    service = DashboardService(db)
    raw = service.get_sd_matrix(week)

    segments = []
    for s in raw["segments"]:
        quadrant = _compute_quadrant(s["sd_ratio"])
        segments.append(SegmentData(
            segment_id=s["segment_id"],
            segment_name=s["segment_name"],
            demand=s["demand"],
            supply=s["supply"],
            sd_ratio=s["sd_ratio"],
            otw_pct=s["otw_pct"],
            quadrant=quadrant,
            avg_salary=s.get("avg_salary"),
            trend=s.get("trend"),
        ))

    opportunity_segs = [s for s in segments if s.quadrant == "OPPORTUNITY"]
    top_seg = max(segments, key=lambda s: s.sd_ratio) if segments else None

    summary = DashboardSummary(
        total_postings=raw["total_demand"],
        opportunity_segments=len(opportunity_segs),
        avg_sd_ratio=raw["market_sd_ratio"],
        top_opportunity_segment=top_seg.segment_id if top_seg else "",
    )

    return ApiResponse(data=SDMatrixResponse(summary=summary, segments=segments))


@router.get("/sd-matrix/{segment_id}/drilldown", response_model=ApiResponse[dict])
def get_sd_matrix_drilldown(
    segment_id: str,
    week: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """직군 드릴다운 - 특정 직군의 상세 수급 데이터"""
    service = DashboardService(db)
    matrix = service.get_sd_matrix(week)

    seg_data = next((s for s in matrix["segments"] if s["segment_id"] == segment_id), None)
    if not seg_data:
        raise HTTPException(status_code=404, detail=f"직군 '{segment_id}'를 찾을 수 없습니다.")

    trend_raw = service.get_trends(segment_id)
    company_ranks = service.get_company_rankings(segment_id, limit=10)

    drilldown = {
        "segment_id": segment_id,
        "segment_name": seg_data["segment_name"],
        "week": matrix["week"],
        "demand": seg_data["demand"],
        "supply": seg_data["supply"],
        "sd_ratio": seg_data["sd_ratio"],
        "otw_pct": seg_data["otw_pct"],
        "avg_salary": seg_data.get("avg_salary"),
        "top_companies": company_ranks["companies"][:10],
        "weekly_trend": trend_raw["data_points"],
    }
    return ApiResponse(data=drilldown)


@router.get("/companies", response_model=ApiResponse[list[CompanyRankItem]])
def get_top_companies(
    segment_id: str | None = Query(None, description="직군 필터"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """TOP 기업 채용 순위"""
    service = DashboardService(db)
    raw = service.get_company_rankings(segment_id, limit)

    # 현재 주차(DB 최신 기준) 조회 후 WoW 변화량 계산
    company_ids = [c["company_id"] for c in raw["companies"]]
    wow_changes: dict[str, int] = {}
    if company_ids:
        latest_week_row = db.query(func.max(WeeklySnapshot.week)).scalar()
        if latest_week_row:
            wow_changes = service.get_company_wow_changes(company_ids, latest_week_row)

    items = []
    for c in raw["companies"]:
        seg = segment_id or (c["segment_ids"][0] if c["segment_ids"] else "")
        items.append(CompanyRankItem(
            company_id=c["company_id"],
            rank=c["rank"],
            company=c["company_name"],
            segment=seg,
            weekly_count=c["posting_count"],
            positions=[],
            week_over_week_change=wow_changes.get(c["company_id"], 0),
        ))
    return ApiResponse(data=items)


@router.get("/companies/{company_id}", response_model=ApiResponse[dict])
def get_company_detail(
    company_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """기업 상세 정보"""
    service = DashboardService(db)
    data = service.get_company_profile(company_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'를 찾을 수 없습니다.")
    return ApiResponse(data=data)


@router.get("/timeline", response_model=ApiResponse[list[CompanyTimeline]])
def get_timeline(
    company_id: str | None = Query(None, description="기업 ID 필터"),
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """기업 채용 타임라인"""
    service = DashboardService(db)
    raw = service.get_timeline(company_id)

    company_map: dict[str, dict] = {}
    for entry in raw["entries"]:
        cid = entry["company_id"]
        if cid not in company_map:
            company_map[cid] = {"company": entry["company_name"], "weeks": {}}
        week = entry["week"]
        company_map[cid]["weeks"][week] = company_map[cid]["weeks"].get(week, 0) + entry["count"]

    timelines = []
    for cid, info in company_map.items():
        data_points = [
            TimelineDataPoint(week=w, count=cnt)
            for w, cnt in sorted(info["weeks"].items())
        ]
        timelines.append(CompanyTimeline(
            company_id=cid,
            company=info["company"],
            data=data_points,
        ))

    return ApiResponse(data=timelines)


@router.get("/trends", response_model=ApiResponse[list[SegmentTrend]])
def get_trends(
    segment_id: str | None = Query(None, description="직군 필터"),
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """채용 트렌드 (12주 추이)"""
    service = DashboardService(db)
    raw = service.get_trends(segment_id)

    # Group data_points by segment
    seg_map: dict[str, list[dict]] = {}
    for dp in raw["data_points"]:
        sid = dp["segment_id"]
        seg_map.setdefault(sid, [])
        seg_map[sid].append(dp)

    if segment_id:
        # Return only the requested segment
        from app.services.dashboard_service import _segment_name
        pts = seg_map.get(segment_id, [])
        data_points = [TrendDataPoint(week=dp["week"], count=dp["demand"]) for dp in pts]
        trends = [SegmentTrend(
            segment_id=segment_id,
            segment_name=_segment_name(segment_id),
            data=data_points,
        )]
    else:
        from app.services.dashboard_service import _segment_name
        trends = []
        for sid, pts in seg_map.items():
            data_points = [TrendDataPoint(week=dp["week"], count=dp["demand"]) for dp in pts]
            trends.append(SegmentTrend(
                segment_id=sid,
                segment_name=_segment_name(sid),
                data=data_points,
            ))

    return ApiResponse(data=trends)


@router.post("/resume-match", response_model=ApiResponse[ResumeMatchOutput])
def resume_match(
    body: ResumeMatchRequest,
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """이력서 기반 기업 매칭 (MVP: 키워드 매칭)"""
    resume_text = body.resume_text

    skill_keywords = ["Python", "Java", "React", "Vue", "Node.js", "Kubernetes", "AWS", "GCP"]
    found_skills = [kw for kw in skill_keywords if kw.lower() in resume_text.lower()]

    service = DashboardService(db)
    company_data = service.get_resume_match_data(found_skills, limit=body.max_results * 2)

    matches = []
    for c in company_data:
        # 키워드 매칭 기반 점수 계산 (random 대체)
        matched_count = len(found_skills)
        total_keywords = len(skill_keywords)
        base_score = matched_count / total_keywords if total_keywords > 0 else 0.5
        score = round(min(0.95, max(0.1, base_score + 0.3)), 2)
        matches.append(MatchResult(
            company_id=c["company_id"],
            company=c["company_name"],
            score=score,
            segment=c["segment_id"],
            match_reason=f"{c['industry']} 분야 적합" if c["industry"] else "채용 활성 기업",
            matched_skills=found_skills[:3],
            active_postings=c["active_postings"],
        ))

    matches.sort(key=lambda x: x.score, reverse=True)

    return ApiResponse(data=ResumeMatchOutput(
        matches=matches[:body.max_results],
        extracted_keywords=found_skills,
        processing_time_ms=0,
        match_engine="KEYWORD",
    ))


@router.get("/jd-insights", response_model=ApiResponse[JdInsightsResponse])
def get_jd_insights(
    segment_id: str | None = None,
    weeks: int = 12,
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """JD 인사이트 — 기술 트렌드, 경력 분포, 연봉 벤치마크 (PRO+)"""
    service = JdInsightsService(db)
    data = service.get_insights(segment_id=segment_id, weeks=min(weeks, 52))
    return ApiResponse(data=JdInsightsResponse(**data))


@router.get("/company-analysis/{company_id}", response_model=ApiResponse[CompanyProfile])
def get_company_analysis(
    company_id: str,
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """기업 채용 심층 분석"""
    service = DashboardService(db)
    raw = service.get_company_profile(company_id)
    if not raw:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'를 찾을 수 없습니다.")

    # DNA 스냅샷에서 실데이터 조회 (있는 경우)
    from app.services.company_dna_service import CompanyDnaService
    dna_service = CompanyDnaService(db)
    dna = dna_service.get_company_dna(company_id)

    if dna:
        senior_count = dna["hiring"]["role_level_dist"].get("senior", 0)
        total_postings = max(dna["hiring"]["total_postings"], 1)
        talent_density = TalentDensity(
            overall=dna["tech"]["diversity_score"],
            tech_diversity=dna["tech"]["diversity_index"],
            senior_ratio=round(senior_count / total_postings * 100, 1),
            avg_tenure="N/A",  # DNA에서 추론 불가
            internal_otw_pct=raw["otw_pct"],
        )
        recent_trend = [dp["demand"] for dp in raw["hiring_trend"][-4:]]
        hiring_power = HiringPower(
            overall=dna["hiring"]["intensity_score"],
            active_postings=sum(p["count"] for p in raw["recent_postings"]),
            weekly_trend=recent_trend,
        )
    else:
        # DNA 스냅샷 없는 경우 — 기본값
        talent_density = TalentDensity(
            overall=0.0,
            tech_diversity=0.0,
            senior_ratio=0.0,
            avg_tenure="N/A",
            internal_otw_pct=raw["otw_pct"],
        )
        recent_trend = [dp["demand"] for dp in raw["hiring_trend"][-4:]]
        hiring_power = HiringPower(
            overall=0.0,
            active_postings=sum(p["count"] for p in raw["recent_postings"]),
            weekly_trend=recent_trend,
        )

    # DNA 기반 추가 메트릭 계산 (0.0~1.0 클램핑)
    def _clamp(v: float | None) -> float:
        if v is None:
            return 0.0
        return max(0.0, min(1.0, v))

    growth_score = 0.0
    salary_competitiveness = 0.0
    tech_diversity_score = 0.0
    hiring_velocity = 0.0

    if dna:
        # growth_score: growth_velocity → 0~1 정규화 ([-5, +5] 범위 가정, 중앙 0.5)
        gv = dna["hiring"].get("growth_velocity")
        if gv is not None:
            growth_score = _clamp((gv + 5.0) / 10.0)

        # salary_competitiveness: salary_position_pct (0~100) → 0~1
        sp = dna["compensation"].get("position_percentile")
        if sp is not None:
            salary_competitiveness = _clamp(sp / 100.0)

        # tech_diversity: diversity_score (0~100) → 0~1
        td = dna["tech"].get("diversity_score")
        if td is not None:
            tech_diversity_score = _clamp(td / 100.0)

        # hiring_velocity: hiring_intensity_score (0~100) → 0~1
        hi = dna["hiring"].get("intensity_score")
        if hi is not None:
            hiring_velocity = _clamp(hi / 100.0)

    profile = CompanyProfile(
        company_id=company_id,
        name=raw["company_name"],
        talent_density=talent_density,
        hiring_power=hiring_power,
        growth_score=growth_score,
        salary_competitiveness=salary_competitiveness,
        tech_diversity=tech_diversity_score,
        hiring_velocity=hiring_velocity,
    )

    return ApiResponse(data=profile)


@router.get("/company-dna/compare", response_model=ApiResponse[DnaComparisonResponse])
def compare_company_dna(
    company_a: str = Query(..., description="기업 A ID 또는 이름"),
    company_b: str = Query(..., description="기업 B ID 또는 이름"),
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """2개 기업 DNA 비교 — Side-by-side 4축 비교 (PRO+)"""
    from app.services.company_dna_service import CompanyDnaService
    service = CompanyDnaService(db)
    result = service.compare_companies(company_a, company_b)
    if not result:
        raise HTTPException(status_code=404, detail="두 기업 모두 DNA 데이터를 찾을 수 없습니다.")
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(data=DnaComparisonResponse(**result))


@router.get("/company-dna/{company_id}/trend", response_model=ApiResponse[DnaTrendResponse])
def get_company_dna_trend(
    company_id: str,
    weeks: int = Query(12, ge=4, le=52),
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """회사 DNA 트렌드 — 주간 DNA 점수 추이 (PRO+)"""
    from app.services.company_dna_service import CompanyDnaService
    service = CompanyDnaService(db)
    data = service.get_company_dna_trend(company_id, weeks)
    if not data:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'의 DNA 트렌드 데이터를 찾을 수 없습니다.")
    return ApiResponse(data=DnaTrendResponse(**data))


@router.get("/company-dna/{company_id}", response_model=ApiResponse[CompanyDnaResponse])
def get_company_dna(
    company_id: str,
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """회사 DNA 프로필 — Tech/Hiring/Compensation/Culture 4축 분석 (PRO+)"""
    from app.services.company_dna_service import CompanyDnaService
    service = CompanyDnaService(db)
    data = service.get_company_dna(company_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'의 DNA 데이터를 찾을 수 없습니다.")
    return ApiResponse(data=CompanyDnaResponse(**data))


@router.get("/segment-benchmark/{segment_id}", response_model=ApiResponse[SegmentBenchmarkResponse])
def get_segment_benchmark(
    segment_id: str,
    current_user: dict = Depends(require_pro),
    db: Session = Depends(get_db),
):
    """세그먼트 평균 DNA — 기업 DNA 비교 기준선 (PRO+)"""
    from app.services.company_dna_service import CompanyDnaService
    service = CompanyDnaService(db)
    data = service.get_segment_benchmarks(segment_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"세그먼트 '{segment_id}'의 벤치마크 데이터를 찾을 수 없습니다.")
    return ApiResponse(data=SegmentBenchmarkResponse(**data))
