"""JD 파서 테스트 — Anthropic API 모킹"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.jd_parser import JdParserService


SAMPLE_PARSED_JSON = '''{
  "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
  "experience": {"min_years": 3, "max_years": 7, "level": "senior"},
  "compensation": {"salary_min": 5000, "salary_max": 8000, "has_equity": true, "benefits": ["유연근무"]},
  "role_keywords": ["API 설계", "코드리뷰"],
  "domain_knowledge": ["핀테크"],
  "org_signals": {"team_size": "10명", "is_new_position": true, "growth_stage": "scale-up"}
}'''


class TestJdParserService:
    @patch("app.services.jd_parser.settings")
    def test_no_api_key(self, mock_settings):
        """API 키 없으면 클라이언트 미초기화"""
        mock_settings.ANTHROPIC_API_KEY = ""
        parser = JdParserService()
        assert parser._client is None

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_parse_jd_success(self, mock_anthropic_cls, mock_settings):
        """정상 파싱 케이스"""
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.JD_PARSER_MODEL = "claude-haiku-4-5-20251001"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_PARSED_JSON)]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=200)

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        parser = JdParserService()
        result = parser.parse_jd("토스 서버팀에서 시니어 백엔드 개발자를 모집합니다...")

        assert result is not None
        assert "Python" in result["tech_stack"]
        assert result["experience"]["level"] == "senior"
        assert result["compensation"]["salary_min"] == 5000

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_parse_jd_with_code_block(self, mock_anthropic_cls, mock_settings):
        """JSON이 코드 블록으로 감싸진 경우"""
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.JD_PARSER_MODEL = "claude-haiku-4-5-20251001"

        wrapped = f"```json\n{SAMPLE_PARSED_JSON}\n```"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=wrapped)]
        mock_response.usage = MagicMock(input_tokens=500, output_tokens=200)

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        parser = JdParserService()
        result = parser.parse_jd("테스트 JD")

        assert result is not None
        assert "Python" in result["tech_stack"]

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_parse_jd_empty_text(self, mock_anthropic_cls, mock_settings):
        """빈 텍스트 → None"""
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_anthropic_cls.return_value = MagicMock()

        parser = JdParserService()
        assert parser.parse_jd("") is None
        assert parser.parse_jd("   ") is None

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_parse_jd_malformed_json(self, mock_anthropic_cls, mock_settings):
        """잘못된 JSON 응답 → None"""
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.JD_PARSER_MODEL = "claude-haiku-4-5-20251001"

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="이건 JSON이 아닙니다")]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_cls.return_value = mock_client

        parser = JdParserService()
        result = parser.parse_jd("테스트 JD")
        assert result is None

    def test_truncation(self):
        """4000자 초과 텍스트 절삭 — 에러 없이 처리되는지 확인"""
        long_text = "가" * 5000
        # _client가 None이면 None 반환 (ANTHROPIC_API_KEY 미설정 환경)
        parser = JdParserService()
        result = parser.parse_jd(long_text)
        assert result is None

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_apply_parsed_data(self, mock_anthropic_cls, mock_settings):
        """_apply_parsed_data가 파싱 결과를 JdAnalysis에 올바르게 매핑"""
        from unittest.mock import MagicMock, patch
        from app.models.pulse import JdAnalysis

        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.JD_PARSER_MODEL = "claude-haiku-4-5-20251001"
        mock_anthropic_cls.return_value = MagicMock()

        parser = JdParserService()

        # JdAnalysis 모킹 (DB 연결 없이)
        analysis = MagicMock(spec=JdAnalysis)

        parsed_data = {
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "experience": {"min_years": 2, "max_years": 5, "level": "mid"},
            "compensation": {"salary_min": 4000, "salary_max": 7000, "has_equity": False, "benefits": []},
            "role_keywords": ["API 설계", "코드리뷰"],
            "domain_knowledge": ["핀테크", "결제"],
            "org_signals": {"team_size": "10명", "is_new_position": True, "growth_stage": "scale-up"},
        }

        parser._apply_parsed_data(analysis, parsed_data)

        # parsed_data 전체 저장 확인
        assert analysis.parsed_data == parsed_data
        # 모델명 기록 확인
        assert analysis.model_used == "claude-haiku-4-5-20251001"
        # parsed_at 설정 확인
        assert analysis.parsed_at is not None
        # tech_stacks 매핑
        assert analysis.tech_stacks == ["Python", "FastAPI", "PostgreSQL"]
        # experience 매핑
        assert analysis.experience_min == 2
        assert analysis.experience_max == 5
        assert analysis.role_level == "mid"
        # compensation 매핑
        assert analysis.salary_min == 4000
        assert analysis.salary_max == 7000
        # domain_tags 매핑
        assert analysis.domain_tags == ["핀테크", "결제"]

    @patch("app.services.jd_parser.settings")
    @patch("app.services.jd_parser.anthropic.Anthropic")
    def test_parse_jd_api_error(self, mock_anthropic_cls, mock_settings):
        """Anthropic API 오류 발생 시 None 반환 (graceful 처리)"""
        import anthropic as anthropic_module

        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.JD_PARSER_MODEL = "claude-haiku-4-5-20251001"

        mock_client = MagicMock()
        # APIError 생성: request 파라미터 필요
        mock_client.messages.create.side_effect = anthropic_module.APIStatusError(
            message="rate limit exceeded",
            response=MagicMock(status_code=429),
            body={"error": {"type": "rate_limit_error"}},
        )
        mock_anthropic_cls.return_value = mock_client

        parser = JdParserService()
        result = parser.parse_jd("정상적인 JD 텍스트")
        assert result is None
