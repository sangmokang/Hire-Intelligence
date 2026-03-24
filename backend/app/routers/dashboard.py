import random

from fastapi import APIRouter, Depends, Query, HTTPException

from app.dependencies import get_current_user
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
)
from app.seed.dashboard_data import (
    get_sd_matrix_data,
    get_company_rankings as seed_get_company_rankings,
    get_timeline_data,
    get_trend_data,
    get_company_profile,
    SEGMENTS,
    COMPANIES,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


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
async def get_sd_matrix(
    week: str | None = Query(None, description="ISO 주차 (예: 2024-W01)"),
    current_user: dict = Depends(get_current_user),
):
    """수급 매트릭스 - 전체 직군별 수요/공급 현황"""
    raw = get_sd_matrix_data(week)

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
async def get_sd_matrix_drilldown(
    segment_id: str,
    week: str | None = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """직군 드릴다운 - 특정 직군의 상세 수급 데이터"""
    segment = next((s for s in SEGMENTS if s["id"] == segment_id), None)
    if not segment:
        raise HTTPException(status_code=404, detail=f"직군 '{segment_id}'를 찾을 수 없습니다.")

    matrix = get_sd_matrix_data(week)
    seg_data = next((s for s in matrix["segments"] if s["segment_id"] == segment_id), None)

    trend_data = get_trend_data(segment_id)
    company_ranks = seed_get_company_rankings(segment_id, limit=10)

    drilldown = {
        "segment_id": segment_id,
        "segment_name": segment["name"],
        "week": matrix["week"],
        "demand": seg_data["demand"] if seg_data else 0,
        "supply": seg_data["supply"] if seg_data else 0,
        "sd_ratio": seg_data["sd_ratio"] if seg_data else 1.0,
        "otw_pct": seg_data["otw_pct"] if seg_data else 0.0,
        "avg_salary": seg_data["avg_salary"] if seg_data else None,
        "top_companies": company_ranks["companies"][:10],
        "weekly_trend": trend_data["data_points"],
    }
    return ApiResponse(data=drilldown)


@router.get("/companies", response_model=ApiResponse[list[CompanyRankItem]])
async def get_top_companies(
    segment_id: str | None = Query(None, description="직군 필터"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """TOP 기업 채용 순위"""
    raw = seed_get_company_rankings(segment_id, limit)
    items = []
    for c in raw["companies"]:
        # segment: pick first segment_id or provided filter
        seg = (segment_id or (c["segment_ids"][0] if c["segment_ids"] else ""))
        items.append(CompanyRankItem(
            company_id=c["company_id"],
            rank=c["rank"],
            company=c["company_name"],
            segment=seg,
            weekly_count=c["posting_count"],
            positions=[],
            week_over_week_change=0,
        ))
    return ApiResponse(data=items)


@router.get("/companies/{company_id}", response_model=ApiResponse[dict])
async def get_company_detail(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """기업 상세 정보"""
    data = get_company_profile(company_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'를 찾을 수 없습니다.")
    return ApiResponse(data=data)


@router.get("/timeline", response_model=ApiResponse[list[CompanyTimeline]])
async def get_timeline(
    company_id: str | None = Query(None, description="기업 ID 필터"),
    current_user: dict = Depends(get_current_user),
):
    """기업 채용 타임라인"""
    raw = get_timeline_data(company_id)

    # Group entries by company
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
async def get_trends(
    segment_id: str | None = Query(None, description="직군 필터"),
    current_user: dict = Depends(get_current_user),
):
    """채용 트렌드 (12주 추이)"""
    if segment_id:
        # Single segment trend
        raw = get_trend_data(segment_id)
        seg = next((s for s in SEGMENTS if s["id"] == segment_id), None)
        data_points = [
            TrendDataPoint(week=dp["week"], count=dp["demand"])
            for dp in raw["data_points"]
        ]
        trends = [SegmentTrend(
            segment_id=segment_id,
            segment_name=seg["name"] if seg else segment_id,
            data=data_points,
        )]
    else:
        # All segments
        trends = []
        for seg in SEGMENTS:
            raw = get_trend_data(seg["id"])
            data_points = [
                TrendDataPoint(week=dp["week"], count=dp["demand"])
                for dp in raw["data_points"]
            ]
            trends.append(SegmentTrend(
                segment_id=seg["id"],
                segment_name=seg["name"],
                data=data_points,
            ))

    return ApiResponse(data=trends)


@router.post("/resume-match", response_model=ApiResponse[ResumeMatchOutput])
async def resume_match(
    body: ResumeMatchRequest,
    current_user: dict = Depends(get_current_user),
):
    """이력서 기반 기업 매칭 (MVP: 간단한 키워드 매칭)"""
    resume_text = body.resume_text

    skill_keywords = ["Python", "Java", "React", "Vue", "Node.js", "Kubernetes", "AWS", "GCP"]
    found_skills = [kw for kw in skill_keywords if kw.lower() in resume_text.lower()]

    matches = []
    for company in random.sample(COMPANIES, k=min(10, len(COMPANIES))):
        seg = random.choice(SEGMENTS)
        score = round(random.uniform(0.5, 0.95), 2)
        matches.append(MatchResult(
            company_id=company["id"],
            company=company["name"],
            score=score,
            segment=seg["id"],
            match_reason=f"{company['industry']} 분야 적합",
            matched_skills=found_skills[:3],
            active_postings=random.randint(1, 15),
        ))

    matches.sort(key=lambda x: x.score, reverse=True)

    return ApiResponse(data=ResumeMatchOutput(
        matches=matches[:body.max_results],
        extracted_keywords=found_skills,
        processing_time_ms=0,
        match_engine="KEYWORD",
    ))


@router.get("/company-analysis/{company_id}", response_model=ApiResponse[CompanyProfile])
async def get_company_analysis(
    company_id: str,
    current_user: dict = Depends(get_current_user),
):
    """기업 채용 심층 분석"""
    raw = get_company_profile(company_id)
    if not raw:
        raise HTTPException(status_code=404, detail=f"기업 '{company_id}'를 찾을 수 없습니다.")

    # Build TalentDensity from seed data
    talent_density = TalentDensity(
        overall=round(random.uniform(60, 95), 1),
        tech_diversity=round(random.uniform(55, 85), 1),
        senior_ratio=round(random.uniform(25, 50), 1),
        avg_tenure=f"{random.randint(2, 5)}y{random.randint(0, 11)}m",
        internal_otw_pct=raw["otw_pct"],
    )

    # Build HiringPower from seed data
    recent_trend = [dp["demand"] for dp in raw["hiring_trend"][-4:]]
    hiring_power = HiringPower(
        overall=round(random.uniform(65, 98), 1),
        active_postings=sum(p["count"] for p in raw["recent_postings"]),
        weekly_trend=recent_trend,
    )

    profile = CompanyProfile(
        company_id=company_id,
        name=raw["company_name"],
        talent_density=talent_density,
        hiring_power=hiring_power,
    )

    return ApiResponse(data=profile)
