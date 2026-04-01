"""이메일 HTML 템플릿 모음.

모든 CSS는 인라인 style 속성 사용 (이메일 클라이언트 호환).
브랜드 컬러: #2563EB (primary blue), #1E293B (dark text)
반응형 max-width: 600px
"""

from __future__ import annotations


# 공통 이메일 래퍼 HTML
_BASE_STYLE = """
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    background-color: #F8FAFC;
    margin: 0;
    padding: 0;
""".strip()

_CONTAINER_STYLE = """
    max-width: 600px;
    margin: 32px auto;
    background-color: #FFFFFF;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
""".strip()

_HEADER_STYLE = """
    background-color: #2563EB;
    padding: 28px 32px;
""".strip()

_BODY_STYLE = """
    padding: 32px;
    color: #1E293B;
""".strip()

_FOOTER_STYLE = """
    padding: 20px 32px;
    background-color: #F1F5F9;
    color: #64748B;
    font-size: 12px;
    text-align: center;
""".strip()


def weekly_report_template(data: dict) -> str:
    """주간 채용 트렌드 리포트 HTML 템플릿.

    Args:
        data: 리포트 데이터 딕셔너리
            - week: str (예: "2026-W14")
            - top_companies: list[dict] — 상위 5개 기업
              각 항목: {"name": str, "jd_count": int, "change": int}
            - sd_summary: dict — 수급 매트릭스 요약
              {"excess_count": int, "balanced_count": int, "shortage_count": int}
            - trends: list[dict] — 주간 트렌드
              각 항목: {"skill": str, "change_pct": float}

    Returns:
        완성된 HTML 문자열
    """
    week: str = data.get("week", "")
    top_companies: list[dict] = data.get("top_companies", [])
    sd_summary: dict = data.get("sd_summary", {})
    trends: list[dict] = data.get("trends", [])

    # 상위 기업 테이블 행 생성
    company_rows = ""
    for idx, company in enumerate(top_companies[:5], start=1):
        name = company.get("name", "")
        jd_count = company.get("jd_count", 0)
        change = company.get("change", 0)
        change_color = "#16A34A" if change >= 0 else "#DC2626"
        change_sign = "+" if change > 0 else ""
        company_rows += f"""
        <tr style="border-bottom: 1px solid #E2E8F0;">
            <td style="padding: 10px 8px; color: #64748B; width: 32px;">{idx}</td>
            <td style="padding: 10px 8px; font-weight: 500;">{name}</td>
            <td style="padding: 10px 8px; text-align: right;">{jd_count}건</td>
            <td style="padding: 10px 8px; text-align: right; color: {change_color}; font-weight: 600;">{change_sign}{change}</td>
        </tr>"""

    # 수급 매트릭스 요약 배지
    excess = sd_summary.get("excess_count", 0)
    balanced = sd_summary.get("balanced_count", 0)
    shortage = sd_summary.get("shortage_count", 0)

    # 트렌드 목록 생성
    trend_items = ""
    for trend in trends[:5]:
        skill = trend.get("skill", "")
        change_pct = trend.get("change_pct", 0.0)
        color = "#16A34A" if change_pct >= 0 else "#DC2626"
        sign = "+" if change_pct > 0 else ""
        trend_items += f"""
        <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #F1F5F9;">
            <span style="color: #1E293B;">{skill}</span>
            <span style="color: {color}; font-weight: 600;">{sign}{change_pct:.1f}%</span>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>주간 채용 트렌드 리포트 {week}</title>
</head>
<body style="{_BASE_STYLE}">
  <div style="{_CONTAINER_STYLE}">

    <!-- 헤더 -->
    <div style="{_HEADER_STYLE}">
      <p style="margin: 0 0 4px 0; color: #BFDBFE; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">Hire Intelligence</p>
      <h1 style="margin: 0; color: #FFFFFF; font-size: 22px; font-weight: 700;">주간 채용 트렌드 리포트</h1>
      <p style="margin: 6px 0 0 0; color: #BFDBFE; font-size: 14px;">{week}</p>
    </div>

    <!-- 본문 -->
    <div style="{_BODY_STYLE}">

      <!-- Top 5 기업 -->
      <h2 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: #1E293B;">Top 5 채용 기업</h2>
      <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
        <thead>
          <tr style="background-color: #F8FAFC;">
            <th style="padding: 8px; text-align: left; color: #64748B; font-weight: 500;">#</th>
            <th style="padding: 8px; text-align: left; color: #64748B; font-weight: 500;">기업명</th>
            <th style="padding: 8px; text-align: right; color: #64748B; font-weight: 500;">공고 수</th>
            <th style="padding: 8px; text-align: right; color: #64748B; font-weight: 500;">전주 대비</th>
          </tr>
        </thead>
        <tbody>
          {company_rows}
        </tbody>
      </table>

      <!-- 수급 매트릭스 요약 -->
      <h2 style="margin: 28px 0 16px 0; font-size: 16px; font-weight: 700; color: #1E293B;">수급 매트릭스 현황</h2>
      <div style="display: flex; gap: 12px; text-align: center;">
        <div style="flex: 1; background-color: #FEF2F2; border-radius: 8px; padding: 16px 8px;">
          <div style="font-size: 24px; font-weight: 700; color: #DC2626;">{shortage}</div>
          <div style="font-size: 12px; color: #64748B; margin-top: 4px;">공급 부족</div>
        </div>
        <div style="flex: 1; background-color: #F0FDF4; border-radius: 8px; padding: 16px 8px;">
          <div style="font-size: 24px; font-weight: 700; color: #16A34A;">{balanced}</div>
          <div style="font-size: 12px; color: #64748B; margin-top: 4px;">균형</div>
        </div>
        <div style="flex: 1; background-color: #EFF6FF; border-radius: 8px; padding: 16px 8px;">
          <div style="font-size: 24px; font-weight: 700; color: #2563EB;">{excess}</div>
          <div style="font-size: 12px; color: #64748B; margin-top: 4px;">공급 과잉</div>
        </div>
      </div>

      <!-- 주간 스킬 트렌드 -->
      <h2 style="margin: 28px 0 16px 0; font-size: 16px; font-weight: 700; color: #1E293B;">주간 스킬 트렌드</h2>
      <div style="font-size: 14px;">
        {trend_items}
      </div>

      <!-- CTA 버튼 -->
      <div style="margin-top: 32px; text-align: center;">
        <a href="https://valuehire.cc/dashboard"
           style="display: inline-block; background-color: #2563EB; color: #FFFFFF; text-decoration: none;
                  padding: 12px 28px; border-radius: 6px; font-size: 14px; font-weight: 600;">
          전체 리포트 보기
        </a>
      </div>

    </div>

    <!-- 푸터 -->
    <div style="{_FOOTER_STYLE}">
      <p style="margin: 0 0 4px 0;">Hire Intelligence · <a href="https://valuehire.cc" style="color: #2563EB; text-decoration: none;">valuehire.cc</a></p>
      <p style="margin: 0;">수신을 원하지 않으시면 <a href="https://valuehire.cc/settings" style="color: #2563EB; text-decoration: none;">여기서 수신 설정</a>을 변경하세요.</p>
    </div>

  </div>
</body>
</html>"""


def welcome_template(user_name: str) -> str:
    """가입 환영 이메일 HTML 템플릿.

    Args:
        user_name: 사용자 이름 (표시용)

    Returns:
        완성된 HTML 문자열
    """
    # 주요 기능 소개 카드 목록
    features = [
        ("채용 트렌드 분석", "실시간 JD 데이터를 기반으로 산업별 채용 트렌드를 시각화합니다.", "#2563EB"),
        ("수급 매트릭스", "직군별 인재 수급 불균형을 한눈에 파악하세요.", "#7C3AED"),
        ("레쥬메 매칭", "AI가 JD와 이력서를 분석해 최적의 매칭 점수를 제공합니다.", "#059669"),
        ("기업 DNA 분석", "기업별 채용 패턴과 선호 스킬셋을 심층 분석합니다.", "#D97706"),
    ]

    feature_cards = ""
    for title, desc, color in features:
        feature_cards += f"""
        <div style="padding: 16px; border-left: 3px solid {color}; background-color: #F8FAFC;
                    border-radius: 0 6px 6px 0; margin-bottom: 12px;">
          <div style="font-weight: 600; color: #1E293B; margin-bottom: 4px;">{title}</div>
          <div style="font-size: 13px; color: #64748B; line-height: 1.5;">{desc}</div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hire Intelligence에 오신 것을 환영합니다</title>
</head>
<body style="{_BASE_STYLE}">
  <div style="{_CONTAINER_STYLE}">

    <!-- 헤더 -->
    <div style="{_HEADER_STYLE}">
      <p style="margin: 0 0 4px 0; color: #BFDBFE; font-size: 13px; letter-spacing: 0.05em; text-transform: uppercase;">Hire Intelligence</p>
      <h1 style="margin: 0; color: #FFFFFF; font-size: 22px; font-weight: 700;">환영합니다, {user_name}님!</h1>
      <p style="margin: 6px 0 0 0; color: #BFDBFE; font-size: 14px;">채용 인텔리전스 대시보드에 가입해 주셔서 감사합니다.</p>
    </div>

    <!-- 본문 -->
    <div style="{_BODY_STYLE}">

      <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.7; color: #334155;">
        Hire Intelligence는 실시간 채용 데이터를 AI로 분석해 채용 담당자와 구직자 모두에게
        유의미한 인사이트를 제공합니다. 아래 주요 기능을 살펴보세요.
      </p>

      <!-- 기능 소개 카드 -->
      <h2 style="margin: 0 0 16px 0; font-size: 16px; font-weight: 700; color: #1E293B;">주요 기능</h2>
      {feature_cards}

      <!-- 시작하기 버튼 -->
      <div style="margin-top: 32px; text-align: center;">
        <a href="https://valuehire.cc/dashboard"
           style="display: inline-block; background-color: #2563EB; color: #FFFFFF; text-decoration: none;
                  padding: 14px 32px; border-radius: 6px; font-size: 15px; font-weight: 600;">
          대시보드 시작하기
        </a>
      </div>

      <p style="margin: 24px 0 0 0; font-size: 13px; color: #94A3B8; text-align: center;">
        궁금한 점이 있으시면 <a href="mailto:support@hire-intelligence.co.kr" style="color: #2563EB; text-decoration: none;">support@hire-intelligence.co.kr</a>로 연락해 주세요.
      </p>

    </div>

    <!-- 푸터 -->
    <div style="{_FOOTER_STYLE}">
      <p style="margin: 0 0 4px 0;">Hire Intelligence · <a href="https://valuehire.cc" style="color: #2563EB; text-decoration: none;">valuehire.cc</a></p>
      <p style="margin: 0;">본 메일은 회원가입 시 발송되는 안내 메일입니다.</p>
    </div>

  </div>
</body>
</html>"""
