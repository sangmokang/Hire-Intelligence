"""
한국 IT 채용 시장 시드 데이터
실제 서비스 이전 개발/데모용 데이터
"""

from datetime import datetime, timedelta
import random

# 14개 직군 정의
SEGMENTS = [
    {"id": "frontend", "name": "프론트엔드"},
    {"id": "backend", "name": "백엔드"},
    {"id": "fullstack", "name": "풀스택"},
    {"id": "data-engineer", "name": "데이터엔지니어"},
    {"id": "ml-ai", "name": "ML/AI"},
    {"id": "devops-sre", "name": "DevOps/SRE"},
    {"id": "mobile-ios", "name": "모바일(iOS)"},
    {"id": "mobile-android", "name": "모바일(Android)"},
    {"id": "qa-test", "name": "QA/테스트"},
    {"id": "security", "name": "보안"},
    {"id": "pm-po", "name": "PM/PO"},
    {"id": "design-ux", "name": "디자인(UX/UI)"},
    {"id": "data-analyst", "name": "데이터분석"},
    {"id": "infra-cloud", "name": "인프라/클라우드"},
]

# 50개 한국 주요 기업
COMPANIES = [
    {"id": "samsung", "name": "삼성전자", "industry": "반도체/전자", "size": "대기업"},
    {"id": "naver", "name": "네이버", "industry": "인터넷/IT", "size": "대기업"},
    {"id": "kakao", "name": "카카오", "industry": "인터넷/IT", "size": "대기업"},
    {"id": "line", "name": "라인플러스", "industry": "인터넷/IT", "size": "대기업"},
    {"id": "coupang", "name": "쿠팡", "industry": "이커머스", "size": "대기업"},
    {"id": "baemin", "name": "배달의민족(우아한형제들)", "industry": "푸드테크", "size": "대기업"},
    {"id": "toss", "name": "토스(비바리퍼블리카)", "industry": "핀테크", "size": "중견기업"},
    {"id": "danggeun", "name": "당근마켓", "industry": "로컬커머스", "size": "중견기업"},
    {"id": "krafton", "name": "크래프톤", "industry": "게임", "size": "대기업"},
    {"id": "ncsoft", "name": "엔씨소프트", "industry": "게임", "size": "대기업"},
    {"id": "netmarble", "name": "넷마블", "industry": "게임", "size": "대기업"},
    {"id": "nexon", "name": "넥슨코리아", "industry": "게임", "size": "대기업"},
    {"id": "kakaobank", "name": "카카오뱅크", "industry": "핀테크/은행", "size": "중견기업"},
    {"id": "kakao-pay", "name": "카카오페이", "industry": "핀테크", "size": "중견기업"},
    {"id": "hyperconnect", "name": "하이퍼커넥트", "industry": "영상통신", "size": "중견기업"},
    {"id": "musinsa", "name": "무신사", "industry": "패션테크", "size": "중견기업"},
    {"id": "zigbang", "name": "직방", "industry": "프롭테크", "size": "중견기업"},
    {"id": "yanolja", "name": "야놀자", "industry": "여행테크", "size": "대기업"},
    {"id": "kakao-mobility", "name": "카카오모빌리티", "industry": "모빌리티", "size": "중견기업"},
    {"id": "socar", "name": "쏘카", "industry": "모빌리티", "size": "중견기업"},
    {"id": "lguplus", "name": "LG유플러스", "industry": "통신", "size": "대기업"},
    {"id": "skt", "name": "SK텔레콤", "industry": "통신", "size": "대기업"},
    {"id": "kt", "name": "KT", "industry": "통신", "size": "대기업"},
    {"id": "hyundai-autoever", "name": "현대오토에버", "industry": "모빌리티IT", "size": "대기업"},
    {"id": "samsung-sds", "name": "삼성SDS", "industry": "IT서비스", "size": "대기업"},
    {"id": "lg-cns", "name": "LG CNS", "industry": "IT서비스", "size": "대기업"},
    {"id": "sk-c&c", "name": "SK C&C", "industry": "IT서비스", "size": "대기업"},
    {"id": "kbcard", "name": "KB국민카드", "industry": "핀테크/금융", "size": "대기업"},
    {"id": "shinhan-ds", "name": "신한DS", "industry": "금융IT", "size": "대기업"},
    {"id": "kakao-enterprise", "name": "카카오엔터프라이즈", "industry": "클라우드/AI", "size": "중견기업"},
    {"id": "ncloud", "name": "네이버클라우드", "industry": "클라우드", "size": "중견기업"},
    {"id": "wemakeprice", "name": "위메프", "industry": "이커머스", "size": "중견기업"},
    {"id": "11st", "name": "11번가", "industry": "이커머스", "size": "대기업"},
    {"id": "gmarket", "name": "지마켓", "industry": "이커머스", "size": "대기업"},
    {"id": "olive-young", "name": "올리브영", "industry": "뷰티테크", "size": "중견기업"},
    {"id": "melon", "name": "멜론컴퍼니", "industry": "음악스트리밍", "size": "중견기업"},
    {"id": "nhn", "name": "NHN", "industry": "인터넷/IT", "size": "대기업"},
    {"id": "kakao-games", "name": "카카오게임즈", "industry": "게임", "size": "중견기업"},
    {"id": "smilegate", "name": "스마일게이트", "industry": "게임", "size": "대기업"},
    {"id": "pearl-abyss", "name": "펄어비스", "industry": "게임", "size": "중견기업"},
    {"id": "shinsegae-it", "name": "신세계아이앤씨", "industry": "리테일IT", "size": "대기업"},
    {"id": "lotte-it", "name": "롯데정보통신", "industry": "리테일IT", "size": "대기업"},
    {"id": "ridibooks", "name": "리디", "industry": "콘텐츠테크", "size": "중견기업"},
    {"id": "karrot", "name": "당근(Karrot)", "industry": "로컬커머스", "size": "중견기업"},
    {"id": "wanted", "name": "원티드랩", "industry": "HR테크", "size": "중견기업"},
    {"id": "jobkorea", "name": "잡코리아", "industry": "HR테크", "size": "중견기업"},
    {"id": "saramin", "name": "사람인HR", "industry": "HR테크", "size": "중견기업"},
    {"id": "greenlabs", "name": "그린랩스", "industry": "애그테크", "size": "중소기업"},
    {"id": "viva-republica", "name": "비바리퍼블리카", "industry": "핀테크", "size": "중견기업"},
    {"id": "modusign", "name": "모두싸인", "industry": "리걸테크", "size": "중소기업"},
]


def _get_week_labels(num_weeks: int = 12) -> list[str]:
    """최근 N주 ISO 주차 레이블 생성"""
    today = datetime.now()
    weeks = []
    for i in range(num_weeks - 1, -1, -1):
        d = today - timedelta(weeks=i)
        year = d.isocalendar()[0]
        week = d.isocalendar()[1]
        weeks.append(f"{year}-W{week:02d}")
    return weeks


def get_sd_matrix_data(week: str | None = None) -> dict:
    """수급 매트릭스 데이터 반환"""
    if week is None:
        weeks = _get_week_labels(1)
        week = weeks[0]

    # 직군별 수급 데이터 (현실적인 한국 시장 기반)
    segment_config = {
        "frontend":       {"demand": 1820, "supply": 1340, "otw": 42.3, "salary": 5800},
        "backend":        {"demand": 2150, "supply": 1580, "otw": 38.7, "salary": 6200},
        "fullstack":      {"demand": 980,  "supply": 890,  "otw": 35.2, "salary": 5900},
        "data-engineer":  {"demand": 720,  "supply": 480,  "otw": 51.8, "salary": 7100},
        "ml-ai":          {"demand": 890,  "supply": 520,  "otw": 55.4, "salary": 7800},
        "devops-sre":     {"demand": 540,  "supply": 320,  "otw": 48.9, "salary": 7500},
        "mobile-ios":     {"demand": 380,  "supply": 290,  "otw": 40.1, "salary": 6100},
        "mobile-android": {"demand": 420,  "supply": 310,  "otw": 41.5, "salary": 6000},
        "qa-test":        {"demand": 290,  "supply": 380,  "otw": 28.6, "salary": 4800},
        "security":       {"demand": 210,  "supply": 140,  "otw": 33.2, "salary": 7200},
        "pm-po":          {"demand": 650,  "supply": 720,  "otw": 44.7, "salary": 6500},
        "design-ux":      {"demand": 480,  "supply": 560,  "otw": 36.9, "salary": 5200},
        "data-analyst":   {"demand": 560,  "supply": 480,  "otw": 47.3, "salary": 5600},
        "infra-cloud":    {"demand": 410,  "supply": 270,  "otw": 46.1, "salary": 7300},
    }

    segments = []
    total_demand = 0
    total_supply = 0

    for seg in SEGMENTS:
        cfg = segment_config.get(seg["id"], {"demand": 300, "supply": 250, "otw": 35.0, "salary": 5500})
        # 약간의 랜덤 변동 추가
        demand = cfg["demand"] + random.randint(-50, 50)
        supply = cfg["supply"] + random.randint(-30, 30)
        sd_ratio = round(demand / supply, 2) if supply > 0 else 1.0

        segments.append({
            "segment_id": seg["id"],
            "segment_name": seg["name"],
            "demand": demand,
            "supply": supply,
            "sd_ratio": sd_ratio,
            "otw_pct": cfg["otw"],
            "avg_salary": cfg["salary"],
            "trend": "up" if sd_ratio > 1.3 else ("down" if sd_ratio < 0.9 else "stable"),
        })
        total_demand += demand
        total_supply += supply

    return {
        "week": week,
        "segments": segments,
        "total_demand": total_demand,
        "total_supply": total_supply,
        "market_sd_ratio": round(total_demand / total_supply, 2) if total_supply > 0 else 1.0,
    }


def get_company_rankings(segment_id: str | None = None, limit: int = 20) -> dict:
    """TOP 기업 채용 순위 반환"""
    weeks = _get_week_labels(1)
    week = weeks[0]

    companies = []
    for i, company in enumerate(COMPANIES[:limit]):
        posting_count = random.randint(5, 80)
        companies.append({
            "rank": i + 1,
            "company_id": company["id"],
            "company_name": company["name"],
            "industry": company["industry"],
            "size": company["size"],
            "posting_count": posting_count,
            "segment_ids": [s["id"] for s in random.sample(SEGMENTS, k=random.randint(2, 5))],
            "otw_pct": round(random.uniform(25, 60), 1),
            "avg_salary": round(random.uniform(4500, 9000), 0),
        })

    # 공고 수 기준 정렬
    companies.sort(key=lambda x: x["posting_count"], reverse=True)
    for i, c in enumerate(companies):
        c["rank"] = i + 1

    return {
        "week": week,
        "segment_id": segment_id,
        "companies": companies,
        "total": len(COMPANIES),
    }


def get_timeline_data(company_id: str | None = None) -> dict:
    """채용 타임라인 데이터 반환"""
    weeks = _get_week_labels(12)
    entries = []

    target_companies = [c for c in COMPANIES if c["id"] == company_id] if company_id else COMPANIES[:10]

    for company in target_companies[:5]:
        for week in weeks:
            if random.random() > 0.3:  # 70% 확률로 이벤트 생성
                entries.append({
                    "week": week,
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "event_type": random.choice(["new_posting", "closed", "spike"]),
                    "segment_id": random.choice(SEGMENTS)["id"],
                    "count": random.randint(1, 20),
                    "description": f"{company['name']} 채용 활동",
                })

    return {
        "company_id": company_id,
        "entries": entries,
        "weeks": weeks,
    }


def get_trend_data(segment_id: str | None = None) -> dict:
    """채용 트렌드 데이터 반환 (12주)"""
    weeks = _get_week_labels(12)

    # 기준 수치에서 주마다 변동
    base_demand = 1500
    base_supply = 1100
    data_points = []

    for i, week in enumerate(weeks):
        # 점진적 트렌드 + 랜덤 변동
        trend_factor = 1 + (i * 0.01)
        demand = int(base_demand * trend_factor + random.randint(-100, 100))
        supply = int(base_supply * trend_factor + random.randint(-80, 80))
        sd_ratio = round(demand / supply, 2) if supply > 0 else 1.0

        data_points.append({
            "week": week,
            "demand": demand,
            "supply": supply,
            "sd_ratio": sd_ratio,
            "otw_pct": round(random.uniform(30, 55), 1),
        })

    segment_name = None
    if segment_id:
        seg = next((s for s in SEGMENTS if s["id"] == segment_id), None)
        segment_name = seg["name"] if seg else segment_id

    return {
        "segment_id": segment_id,
        "segment_name": segment_name,
        "data_points": data_points,
        "period_weeks": 12,
    }


def get_company_profile(company_id: str) -> dict | None:
    """기업 상세 프로필 반환"""
    company = next((c for c in COMPANIES if c["id"] == company_id), None)
    if not company:
        return None

    weeks = _get_week_labels(12)
    hiring_trend = []
    base = random.randint(10, 50)
    for week in weeks:
        demand = base + random.randint(-5, 15)
        supply = int(demand * 0.7) + random.randint(-3, 5)
        hiring_trend.append({
            "week": week,
            "demand": demand,
            "supply": supply,
            "sd_ratio": round(demand / supply, 2) if supply > 0 else 1.0,
            "otw_pct": round(random.uniform(25, 55), 1),
        })

    recent_postings = []
    for seg in random.sample(SEGMENTS, k=random.randint(2, 5)):
        recent_postings.append({
            "segment_id": seg["id"],
            "segment_name": seg["name"],
            "count": random.randint(1, 15),
            "week": weeks[-1],
        })

    return {
        "company_id": company_id,
        "company_name": company["name"],
        "industry": company["industry"],
        "size": company["size"],
        "segment_ids": [s["id"] for s in random.sample(SEGMENTS, k=3)],
        "recent_postings": recent_postings,
        "hiring_trend": hiring_trend,
        "otw_pct": round(random.uniform(30, 55), 1),
        "avg_salary": round(random.uniform(5000, 9000), 0),
        "summary": f"{company['name']}은(는) {company['industry']} 분야의 {company['size']}입니다.",
    }
