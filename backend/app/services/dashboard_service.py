from app.seed.dashboard_data import (
    get_sd_matrix_data,
    get_company_rankings,
    get_timeline_data,
    get_trend_data,
    get_company_profile,
)


class DashboardService:
    """대시보드 데이터 서비스 (현재 시드 데이터 사용)"""

    async def get_sd_matrix(self, week: str | None = None) -> dict:
        """수급 매트릭스 데이터"""
        return get_sd_matrix_data(week)

    async def get_company_rankings(self, segment_id: str | None = None, limit: int = 20) -> dict:
        """기업 순위"""
        return get_company_rankings(segment_id, limit)

    async def get_timeline(self, company_id: str | None = None) -> dict:
        """타임라인 데이터"""
        return get_timeline_data(company_id)

    async def get_trends(self, segment_id: str | None = None) -> dict:
        """트렌드 데이터"""
        return get_trend_data(segment_id)

    async def get_company_profile(self, company_id: str) -> dict | None:
        """기업 프로필"""
        return get_company_profile(company_id)
