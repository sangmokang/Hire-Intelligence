"""
세그먼트 상수 정의 — 크롤러 세그먼트 ID와 표시 이름을 중앙 관리
14개 표준 세그먼트: 개발(dev_*), 비즈니스(biz), 크리에이티브(creative)
"""
from typing import TypedDict, Literal


class SegmentInfo(TypedDict):
    id: str
    name_ko: str
    name_en: str
    category: Literal["dev", "biz", "creative"]


# 14개 표준 크롤러 세그먼트 정의
SEGMENTS: list[SegmentInfo] = [
    {"id": "dev_server",   "name_ko": "서버/백엔드",   "name_en": "Server/Backend",   "category": "dev"},
    {"id": "dev_frontend", "name_ko": "프론트엔드",    "name_en": "Frontend",          "category": "dev"},
    {"id": "dev_devops",   "name_ko": "DevOps/클라우드", "name_en": "DevOps/Cloud",    "category": "dev"},
    {"id": "dev_mlai",     "name_ko": "ML/AI",         "name_en": "ML/AI",             "category": "dev"},
    {"id": "dev_java",     "name_ko": "Java/안드로이드", "name_en": "Java/Android",     "category": "dev"},
    {"id": "dev_cto",      "name_ko": "개발리드/CTO",   "name_en": "Dev Lead/CTO",     "category": "dev"},
    {"id": "dev_total",    "name_ko": "SW엔지니어링",   "name_en": "SW Engineering",   "category": "dev"},
    {"id": "design",       "name_ko": "UX/UI 디자인",   "name_en": "UX/UI Design",     "category": "creative"},
    {"id": "pm_po",        "name_ko": "Product",       "name_en": "Product",           "category": "biz"},
    {"id": "marketing",    "name_ko": "마케팅",         "name_en": "Marketing",         "category": "biz"},
    {"id": "hr",           "name_ko": "HR",             "name_en": "HR",                "category": "biz"},
    {"id": "cfo_finance",  "name_ko": "재무",           "name_en": "Finance",           "category": "biz"},
    {"id": "sales",        "name_ko": "영업",           "name_en": "Sales",             "category": "biz"},
    {"id": "strategy",     "name_ko": "전략/기획",      "name_en": "Strategy",          "category": "biz"},
]

# 구 대시보드 세그먼트 ID → 표준 ID 매핑 (하위 호환성 유지)
LEGACY_TO_CANONICAL: dict[str, str] = {
    "backend":  "dev_server",
    "frontend": "dev_frontend",
    "ml_ai":    "dev_mlai",
    "devops":   "dev_devops",
    "mobile":   "dev_total",
    "data":     "dev_mlai",
    "security": "dev_devops",
    "fullstack": "dev_total",
}

# 프론트엔드 세그먼트 ID → 표준 ID 매핑
FE_TO_CANONICAL: dict[str, str] = {
    "sw":    "dev_total",
    "data":  "dev_mlai",
    "sales": "sales",
    "prod":  "pm_po",
    "ops":   "dev_devops",
    "mfg":   "dev_total",
    "mktg":  "marketing",
    "fin":   "cfo_finance",
    "hr":    "hr",
    "ux":    "design",
    "legal": "strategy",
    "scm":   "dev_total",
    "rd":    "dev_mlai",
    "med":   "dev_total",
}

# 빠른 조회용 인덱스: 표준 ID → SegmentInfo
_SEGMENT_MAP: dict[str, SegmentInfo] = {s["id"]: s for s in SEGMENTS}


def to_canonical(segment_id: str) -> str:
    """임의의 세그먼트 ID를 표준 ID로 변환. 이미 표준이면 그대로 반환."""
    if segment_id in _SEGMENT_MAP:
        return segment_id
    if segment_id in LEGACY_TO_CANONICAL:
        return LEGACY_TO_CANONICAL[segment_id]
    if segment_id in FE_TO_CANONICAL:
        return FE_TO_CANONICAL[segment_id]
    return segment_id


def get_segment_name(segment_id: str) -> str:
    """세그먼트 ID로 한국어 이름 조회. 레거시 ID도 자동 변환."""
    canonical = to_canonical(segment_id)
    seg = _SEGMENT_MAP.get(canonical)
    return seg["name_ko"] if seg else segment_id


def get_all_segments() -> list[SegmentInfo]:
    """전체 표준 세그먼트 목록 반환."""
    return list(SEGMENTS)
