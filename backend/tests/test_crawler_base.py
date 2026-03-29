"""크롤러 기본 유틸리티 테스트"""
import pytest
from app.services.crawler.base import (
    normalize_company_name,
    jaccard_similarity,
    is_duplicate_title,
)


class TestNormalizeCompanyName:
    def test_remove_inc(self):
        assert normalize_company_name("Toss Inc.") == "Toss"

    def test_remove_korean_suffix(self):
        assert normalize_company_name("카카오(주)") == "카카오"

    def test_remove_corp(self):
        assert normalize_company_name("Samsung Corp") == "Samsung"

    def test_remove_ltd(self):
        assert normalize_company_name("NAVER Co., Ltd.") == "NAVER"

    def test_strip_whitespace(self):
        assert normalize_company_name("  토스  ") == "토스"

    def test_no_suffix(self):
        assert normalize_company_name("네이버") == "네이버"

    def test_multiple_spaces(self):
        assert normalize_company_name("토스  뱅크") == "토스 뱅크"


class TestJaccardSimilarity:
    def test_identical(self):
        assert jaccard_similarity("시니어 백엔드 개발자", "시니어 백엔드 개발자") == 1.0

    def test_similar(self):
        # "시니어", "백엔드", "개발자" vs "Senior", "백엔드", "개발자" → 2/4 겹침
        sim = jaccard_similarity("시니어 백엔드 개발자", "Senior 백엔드 개발자")
        assert sim >= 0.5

    def test_different(self):
        sim = jaccard_similarity("프론트엔드 개발자", "마케팅 매니저")
        assert sim < 0.3

    def test_empty(self):
        assert jaccard_similarity("", "test") == 0.0
        assert jaccard_similarity("test", "") == 0.0


class TestIsDuplicateTitle:
    def test_duplicate_found(self):
        existing = ["시니어 백엔드 개발자", "주니어 프론트엔드"]
        assert is_duplicate_title("시니어 백엔드 개발자", existing) is True

    def test_no_duplicate(self):
        existing = ["프론트엔드 개발자"]
        assert is_duplicate_title("데이터 엔지니어", existing) is False

    def test_empty_existing(self):
        assert is_duplicate_title("개발자", []) is False
