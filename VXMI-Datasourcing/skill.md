---
name: talent-insight
description: "LinkedIn Talent Insights 기반 고객사별 인재 흐름·조직 현황 시계열 분석 스킬. jobmarket DB(Supabase)의 company_weekly 테이블에서 타겟 고객사 목록을 가져와 LinkedIn Talent Insights 페이지에서 Overview + Talent Flow 데이터를 수집 → Supabase 누적 저장. Claude in Chrome MCP 전용. 트리거: 'talent insight', '인재 인사이트', '인재 흐름', 'talent flow', '고객사 분석', '조직 현황', '인력 이동', '인사이트 수집', '회사 분석', 'TI 돌려줘', 'talent insights'"
---

# Talent Insight Intelligence Skill v2.0

## 개요 및 핵심 목적

LinkedIn Talent Insights를 통해 **밸류커넥트 타겟 고객사의 인재 흐름과 조직 현황**을 시계열로 추적합니다.

**데이터 소스**: jobmarket 스킬의 Supabase `company_weekly` 테이블에서 채용 활발 기업(OppScore 상위) 목록 추출
**수집 대상**: LinkedIn Talent Insights의 Overview 탭 + Talent Flow 탭 전체 데이터
**저장**: Supabase 동일 프로젝트에 시계열 누적

**측정 지표:**
- `total_employees` — 회사 총 직원 수 (LinkedIn 기준)
- `employee_growth_12m` — 12개월 직원 증감률 (%)
- `median_tenure` — 중간 재직 기간
- `total_hires_12m` — 최근 12개월 신규 채용 수
- `total_departures_12m` — 최근 12개월 퇴사 수
- `net_headcount_change` — 순 인원 변화
- `talent_flow_details` — 회사 간 인재 이동 상세 (어디서 오고 어디로 가는지)

---

## 보안 정책 — Claude in Chrome 전용 (필수)

> **LinkedIn Talent Insights 접근은 반드시 Claude in Chrome (MCP)만 사용.**
> Playwright MCP, browser_navigate, browser_click 등 헤드리스 브라우저 도구 절대 금지.

| 도구 | 허용 여부 |
|------|----------|
| **Claude in Chrome (MCP)** | 유일하게 허용 |
| Playwright MCP | 절대 금지 |
| browser_navigate / browser_click 등 | 절대 금지 |

**Rate Limiting — 적응형 랜덤 딜레이 시스템 (필수):**

LinkedIn은 자동화 감지에 민감합니다. **세션 상태 추적 + 적응형 딜레이**로 안전하게 수집합니다.

```python
import random
import time

class TISessionState:
    """Talent Insight 수집 세션 상태 관리"""
    def __init__(self):
        self.companies_processed = 0      # 현재 세션 처리 회사 수
        self.delay_multiplier = 1.0       # 적응형 딜레이 배수
        self.last_page_load_ms = 0        # 마지막 페이지 로드 시간
        self.session_start = time.time()

    def human_delay(self, min_sec=2, max_sec=5):
        """적응형 랜덤 딜레이 — 상황에 따라 자동 증가"""
        adjusted_min = min_sec * self.delay_multiplier
        adjusted_max = max_sec * self.delay_multiplier
        delay = random.uniform(adjusted_min, adjusted_max)
        time.sleep(delay)
        return delay

    def record_page_load(self, load_time_ms: int):
        """페이지 로드 시간 기록 → 느리면 딜레이 증가"""
        self.last_page_load_ms = load_time_ms
        if load_time_ms > 8000:  # 8초 이상이면 쓰로틀링 의심
            self.delay_multiplier = min(self.delay_multiplier * 1.5, 3.0)
        elif load_time_ms < 3000 and self.delay_multiplier > 1.0:
            self.delay_multiplier = max(self.delay_multiplier * 0.9, 1.0)

    def company_done(self):
        """회사 1개 처리 완료 기록"""
        self.companies_processed += 1

    def needs_long_break(self) -> bool:
        """10개사마다 장시간 휴식 필요 여부"""
        return self.companies_processed > 0 and self.companies_processed % 10 == 0

    def long_break(self):
        """10개사 처리 후 장시간 휴식"""
        delay = random.uniform(30, 60) * self.delay_multiplier
        time.sleep(delay)
        return delay

# 세션 초기화 (수집 시작 시 1회)
session = TISessionState()

# 사용 예:
# 탭 전환 후: session.human_delay(2, 4)
# 회사 검색 후: session.human_delay(3, 6)
# 회사 간 전환: session.human_delay(5, 10)
# 10개사 처리 후: if session.needs_long_break(): session.long_break()
# 페이지 로드 후: session.record_page_load(load_time_ms)
```

**딜레이 기준 (base × delay_multiplier):**

| 액션 | 최소(초) | 최대(초) | 비고 |
|------|---------|---------|------|
| 탭 클릭 (Overview↔Talent Flow) | 2 | 4 | |
| 회사 검색 입력 후 | 3 | 6 | |
| 페이지 내 스크롤 | 1 | 3 | |
| Detail 페이지 클릭/복귀 | 2 | 5 | |
| **회사 간 전환** | **5** | **10** | |
| 연속 10개사 처리 후 | **30** | **60** | `needs_long_break()` |
| **쓰로틀링 감지 시** | **×1.5** | **최대 ×3.0** | `record_page_load()` |

> **적응형 딜레이 동작:** 페이지 로드 8초 초과 → `delay_multiplier` 1.5배 증가 (최대 3.0배).
> 페이지 로드 3초 미만 → 서서히 1.0배로 복귀. 이를 통해 LinkedIn 쓰로틀링에 자동 대응.

---

## 타겟 회사 목록 — Supabase 연동

### 회사 목록 소스: jobmarket DB의 `company_weekly` 테이블

```sql
-- OppScore 상위 + 최근 스냅샷 기준 타겟 회사 추출
-- ⚠️ 3개 테이블 모두 수집 완료된 회사만 제외 (불완전 수집 방지)
SELECT DISTINCT cw.company
FROM company_weekly cw
LEFT JOIN ti_company_mapping m ON cw.company = m.company
WHERE cw.snapshot_date = (SELECT MAX(snapshot_date) FROM company_weekly)
  AND cw.opp_score >= 55                    -- C등급 이상
  AND cw.company NOT IN (
    -- 3개 테이블 모두 최근 7일 내 데이터가 있는 회사만 제외
    SELECT o.company
    FROM ti_overview o
    INNER JOIN ti_talent_flow_summary f
      ON o.company = f.company AND o.snapshot_date = f.snapshot_date
    INNER JOIN (
      SELECT DISTINCT company, snapshot_date
      FROM ti_talent_flow_detail
    ) d ON o.company = d.company AND o.snapshot_date = d.snapshot_date
    WHERE o.snapshot_date >= CURRENT_DATE - INTERVAL '7 days'
  )
  AND COALESCE(m.status, 'unverified') != 'not_found'  -- 매핑 실패 회사 제외
ORDER BY cw.opp_score DESC
LIMIT 30;                                -- 1회 최대 30개사 (Rate Limiting 고려)
```

> **수동 지정도 가능**: 사용자가 특정 회사명을 직접 입력하면 해당 회사만 수집.

---

## LinkedIn Talent Insights URL 구조

### 진입점

```
기본 URL: https://www.linkedin.com/talent/insights
또는 직접: https://www.linkedin.com/insights/
```

### 탭별 URL 패턴

회사가 선택되면 URL에 인코딩된 회사 ID가 포함됩니다:

```
Overview:     /insights/report/company/{encoded_id}/?module=overview
Talent Flow:  /insights/report/company/{encoded_id}/talent-flow?module=talentFlow
Location:     /insights/report/company/{encoded_id}/location?module=location
Titles:       /insights/report/company/{encoded_id}/titles?module=titles
Skills:       /insights/report/company/{encoded_id}/skills?module=skills
Attrition:    /insights/report/company/{encoded_id}/attrition?module=attrition
Education:    /insights/report/company/{encoded_id}/education?module=education
Profiles:     /insights/report/company/{encoded_id}/profiles?module=profiles
```

### 탭 구조 (스크린샷 기준)

```
┌─────────────────────────────────────────────────────────┐
│  [Company] Bungaejangter Inc.                           │
│  South Korea · Full-time                                │
│  154 employees on LinkedIn                              │
│                                                         │
│  Overview | Location | Talent flow | Titles | Skills |  │
│  Attrition | Education | Profiles                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [현재 탭 콘텐츠]                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘

좌측 사이드바:
  Company (Required): [회사명 입력]
  Location: [South Korea]
  Skill: [+]
  Job Title: [+]
  Function: [+]
  Advanced Filters: [▼]
```

---

## 워크플로우 전체 구조

```
Phase 0: LinkedIn 세션 확인 (li_at 쿠키)
 └─ Claude in Chrome → 페이지 콘텐츠 기반 세션 확인 → 만료 시 수동 로그인 요청

Phase 1: 타겟 회사 목록 확보
 ├─ 1A: Supabase company_weekly에서 OppScore 상위 회사 추출
 │       (⚠️ 3개 테이블 모두 완료된 회사만 제외 — 불완전 수집 방지)
 ├─ 1B: 또는 사용자 직접 지정
 └─ 1C: 회사 매핑 검증 (ti_company_mapping 조회)
         ├─ verified + URL → 직접 접속 목록
         ├─ unverified/미등록 → 검색 필요 목록
         └─ not_found → 스킵 목록

Phase 2: 회사별 데이터 수집 (순회 — 세션 상태 추적)
 ├─ 2A: 매핑 확인 → URL 직접 접속 또는 이름 검색
 │       └─ 검색 성공 시 encoded_id 캡처 → ti_company_mapping 저장
 ├─ 2B: Overview 탭 데이터 수집
 ├─ 2C: Talent Flow 탭 데이터 수집
 │    ├─ 2C-1: 상단 트렌드 차트 (Hires + Departures / Employees)
 │    ├─ 2C-2: 요약 수치 (Total Hires, Departures, Net change)
 │    ├─ 2C-3: 인재 이동 테이블 전체 행 수집 (페이지네이션)
 │    └─ 2C-4: 각 회사 행 클릭 → Detail 팝업 데이터 수집
 └─ 2D: 적응형 딜레이 → session.company_done() → 다음 회사
         └─ 10개사마다 session.long_break() (30~60초)

Phase 3: Supabase 저장 (검증 후)
 ├─ 3A-0: 데이터 검증 (validate_overview, validate_flow_details)
 ├─ 3A: ti_overview upsert
 ├─ 3B: ti_talent_flow_summary upsert
 ├─ 3C: ti_talent_flow_detail upsert
 └─ 3D: ti_collection_log 업데이트 (status='success')

Phase 4: 리포팅
 └─ 4A: 고객사별 인재 인사이트 브리핑 출력
```

---

## Phase 0: LinkedIn 세션 확인

> **LinkedIn 봇 감지 방지를 위해, li_at 쿠키 기반 세션 유지를 사용한다.**
> 로그인 페이지(`linkedin.com/login`)로 직접 navigate하는 것은 절대 금지한다.

### 세션 확인 절차

```
1. tabs_context_mcp로 현재 크롬 탭 목록 조회
2. LinkedIn 탭(linkedin.com 포함) 존재 여부 확인
   ├─ 탭 있음 → 해당 탭으로 이동 (탭 재사용)
   └─ 탭 없음 → 새 탭에서 linkedin.com/insights 접속
3. javascript_tool로 li_at 쿠키 존재 여부 확인:
   ├─ SESSION_VALID → Phase 1로 진행 ✅
   └─ SESSION_EXPIRED → 사용자 수동 로그인 요청 후 대기
```

### li_at 쿠키 체크 코드

> **중요**: li_at 쿠키는 `httpOnly` 속성이므로 `document.cookie`로 접근 불가.
> 대신 **페이지 콘텐츠 기반**으로 세션 유효성을 판단한다.

```javascript
// ❌ 이 방법은 동작하지 않음 (httpOnly)
// document.cookie.includes('li_at') → 항상 false

// ✅ 페이지 콘텐츠 기반 세션 확인
(function() {
  const url = window.location.href;
  // Talent Insights 페이지가 정상 로드되었는지 확인
  if (url.includes('/insights/') || url.includes('/talent/')) {
    const hasContent = document.querySelector('[class*="insight"], [class*="talent"], [class*="report"]');
    const loginPrompt = document.querySelector('[class*="login"], [class*="sign-in"]');
    if (loginPrompt) return 'SESSION_EXPIRED';
    if (hasContent) return 'SESSION_VALID';
  }
  return 'CHECK_MANUALLY';
})()
```

### Talent Insights 접근 권한 확인

```javascript
// Talent Insights 페이지 정상 로드 확인
(function() {
  const url = window.location.href;
  if (url.includes('/insights/')) {
    // 권한 거부 메시지 확인
    const denied = document.querySelector('[data-test-id="access-denied"]');
    if (denied) return 'ACCESS_DENIED';
    return 'ACCESS_OK';
  }
  return 'NOT_ON_INSIGHTS';
})()
```

> **Talent Insights는 LinkedIn Premium 기능입니다.**
> 접근 불가 시 사용자에게 안내: "LinkedIn Talent Insights 접근 권한이 필요합니다. LinkedIn Recruiter 또는 Talent Insights 구독을 확인해주세요."

---

## Phase 1: 타겟 회사 목록 확보

### 1A. Supabase에서 자동 추출

```python
# Supabase REST API 호출 (Claude에서 직접 실행 가능)
import os, json
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_target_companies(min_score=55, limit=30):
    """jobmarket DB에서 타겟 회사 목록 추출 (완전 수집된 회사만 제외)"""
    # 최신 스냅샷 날짜
    latest = (supabase.table("company_weekly")
              .select("snapshot_date")
              .order("snapshot_date", desc=True)
              .limit(1).execute()).data

    if not latest:
        return []

    latest_date = latest[0]['snapshot_date']

    # OppScore 상위 회사
    companies = (supabase.table("company_weekly")
                 .select("company, opp_score, total_positions, platforms")
                 .eq("snapshot_date", latest_date)
                 .gte("opp_score", min_score)
                 .order("opp_score", desc=True)
                 .limit(limit)
                 .execute()).data

    # 최근 7일 내 3개 테이블 모두 수집 완료된 회사만 제외
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=7)).isoformat()

    overview_done = {c['company'] for c in
        (supabase.table("ti_overview").select("company")
         .gte("snapshot_date", cutoff).execute()).data}

    flow_done = {c['company'] for c in
        (supabase.table("ti_talent_flow_summary").select("company")
         .gte("snapshot_date", cutoff).execute()).data}

    detail_done = {c['company'] for c in
        (supabase.rpc("get_distinct_companies_from_detail",
         {"cutoff_date": cutoff}).execute()).data}
    # fallback: detail_done = set() if RPC not available

    # 3개 모두 완료된 회사만 제외
    fully_collected = overview_done & flow_done & detail_done

    # not_found 매핑 제외
    not_found = {c['company'] for c in
        (supabase.table("ti_company_mapping").select("company")
         .eq("status", "not_found").execute()).data}

    return [c for c in companies
            if c['company'] not in fully_collected
            and c['company'] not in not_found]
```

### 1B. 사용자 직접 지정

사용자가 특정 회사를 지정하면 해당 회사만 수집:
```
예: "번개장터 인사이트 봐줘" → ["번개장터"] 만 수집
    "두나무, 뤼튼 인사이트" → ["두나무", "뤼튼테크놀로지스"] 수집
```

### 1C. 회사 매핑 검증 (Phase 1.5)

타겟 회사 목록 확보 후, LinkedIn ID 매핑을 검증합니다.

```python
def validate_company_mappings(target_companies: list) -> tuple:
    """회사 매핑 상태 확인 → (직접접속 가능, 검색 필요, 스킵) 분류"""
    direct_access = []   # verified + URL 있음 → 검색 스킵
    needs_search = []    # unverified 또는 미등록 → 이름 검색
    skip_list = []       # not_found → 7일 내 재시도 불필요

    for c in target_companies:
        mapping = (supabase.table("ti_company_mapping")
                    .select("*")
                    .eq("company", c['company'])
                    .execute()).data

        if mapping:
            m = mapping[0]
            if m['status'] == 'verified' and m.get('linkedin_url'):
                direct_access.append({**c, 'mapping': m})
            elif m['status'] == 'not_found':
                skip_list.append(c)
            else:
                needs_search.append({**c, 'mapping': m})
        else:
            needs_search.append({**c, 'mapping': None})

    return direct_access, needs_search, skip_list
```

**매핑 저장 — 검색 성공 시:**

```python
def save_company_mapping(company: str, linkedin_data: dict):
    """검색 성공 후 매핑 저장 (이후 직접 접속 가능)"""
    row = {
        "company":               company,
        "linkedin_company_id":   linkedin_data.get('encoded_id'),
        "linkedin_company_name": linkedin_data.get('display_name'),
        "linkedin_url":          linkedin_data.get('insights_url'),
        "search_query_used":     linkedin_data.get('search_query'),
        "status":                "verified",
        "verified_at":           "now()",
        "last_used_at":          "now()"
    }
    supabase.table("ti_company_mapping").upsert(row).execute()

def mark_mapping_not_found(company: str, search_query: str):
    """검색 실패 시 not_found 기록 (7일 후 재시도)"""
    row = {
        "company":           company,
        "search_query_used": search_query,
        "status":            "not_found",
        "notes":             f"자동완성 매칭 실패 ({search_query})"
    }
    supabase.table("ti_company_mapping").upsert(row).execute()
```

**URL에서 encoded_id 추출 — JavaScript:**

```javascript
// 회사 선택 후 URL에서 encoded_id 캡처
(function() {
  const url = window.location.href;
  const match = url.match(/\/insights\/report\/company\/([^\/\?]+)/);
  if (match) {
    return JSON.stringify({
      encoded_id: match[1],
      full_url: url,
      display_name: document.querySelector('.artdeco-entity-lockup__title, [class*="company-name"]')?.textContent?.trim() || ''
    });
  }
  return JSON.stringify({ error: 'NOT_ON_COMPANY_PAGE' });
})()
```

---

## Phase 2: 회사별 데이터 수집

### 2A. 회사 검색 및 필터 설정 (매핑 우선)

```
[회사 N 시작 — 세션 카운터: session.companies_processed]

Step 0 — 10개사 쿨다운 체크
  - if session.needs_long_break(): session.long_break()
  - ti_collection_log에 진행 상황 기록

Step 1 — 매핑 확인 후 분기
  ├─ 매핑 verified + linkedin_url 있음:
  │    → URL 직접 접속 (navigate)
  │    → 검색 단계 스킵 → Step 4로 이동
  │    → session.human_delay(3, 6)
  │
  ├─ 매핑 verified + linkedin_company_name만 있음:
  │    → 영문명으로 Company 필드 검색 → Step 2로
  │
  └─ 미등록 또는 unverified:
       → 한글 회사명으로 Company 필드 검색 → Step 2로

Step 2 — Company 필드 초기화 및 입력 (검색 필요 시만)
  - 좌측 "Company (Required)" 필드의 기존 값 Clear 클릭
  - 회사명 입력 (매핑의 linkedin_company_name 또는 한글명)
  - 자동완성 드롭다운에서 정확한 회사 선택
  - ⚠️ 자동완성 매칭 실패 시:
    · mark_mapping_not_found() 호출
    · ti_collection_log에 status='skipped' 기록
    · 다음 회사로 이동
  - session.human_delay(3, 6)

Step 3 — URL에서 encoded_id 캡처 & 매핑 저장
  - javascript_tool로 현재 URL에서 encoded_id 추출
  - save_company_mapping() 호출 → 다음 실행 시 직접 접속 가능
  - session.human_delay(1, 2)

Step 4 — Location 설정
  - Location 필드에 "South Korea" 입력
  - 자동완성에서 "South Korea" 선택
  - ⚠️ 이미 "South Korea"가 설정되어 있으면 스킵
  - session.human_delay(2, 4)

Step 5 — 데이터 로드 대기 & 로드 시간 기록
  - 페이지 콘텐츠 로딩 완료 대기 (최소 3초)
  - 로딩 스피너 사라짐 확인
  - load_start → load_end 측정 → session.record_page_load(load_time_ms)
  - ⚠️ load_time > 8000ms이면 쓰로틀링 의심 → 딜레이 자동 증가

[필터 설정 완료 → 2B로 이동]
```

### 회사 검색 시 JavaScript 보조 코드

```javascript
// Company 필드 Clear 후 입력
(function() {
  // Clear 버튼 찾기
  const clearBtn = document.querySelector('[data-test-company-filter] .artdeco-pill__delete, .search-reusables__filter-value-delete');
  if (clearBtn) clearBtn.click();
  return 'CLEARED';
})()
```

```javascript
// 자동완성 결과 확인
(function() {
  const suggestions = document.querySelectorAll('.basic-typeahead__selectable, .search-typeahead-v2__hit');
  const results = [];
  suggestions.forEach(s => {
    results.push(s.textContent.trim().substring(0, 100));
  });
  return JSON.stringify(results);
})()
```

### 2B. Overview 탭 데이터 수집

Overview 탭에서 수집할 데이터 항목:

```
┌─────────────────────────────────────────────────────────┐
│ Overview 탭 수집 항목                                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. 기본 정보                                             │
│    - 회사명 (영문/한글)                                   │
│    - 직원 수 (LinkedIn 기준): "154 employees on LinkedIn" │
│    - 본사 위치                                           │
│    - 산업군 (Industry)                                   │
│                                                         │
│ 2. 인력 현황 (Headcount)                                 │
│    - 총 직원 수                                          │
│    - 12개월 성장률 (%)                                    │
│    - 부서별 인원 분포 (Function breakdown)                 │
│    - 직급별 분포 (Seniority breakdown)                    │
│                                                         │
│ 3. 채용/이직 현황                                        │
│    - 최근 12개월 신규 채용 수                              │
│    - 최근 12개월 퇴사 수                                  │
│    - 중간 재직 기간 (Median tenure)                       │
│                                                         │
│ 4. 스킬 하이라이트                                       │
│    - 상위 스킬 목록                                      │
│    - 성장 중인 스킬                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**수집 절차:**

```
Step 1 — Overview 탭 클릭
  - "Overview" 탭 링크 클릭
  - 랜덤 딜레이: human_delay(2, 4)

Step 2 — read_page로 페이지 구조 파악
  - read_page(tabId, depth=10) 실행
  - 주요 데이터 영역의 ref_id 식별

Step 3 — 데이터 추출 (get_page_text 또는 javascript_tool)
  - 전체 텍스트 추출 후 파싱
  - 또는 특정 섹션별 DOM 쿼리

Step 4 — 구조화된 데이터로 변환
  - JSON 형태로 정리
```

**Overview 데이터 추출 JavaScript:**

```javascript
// Overview 탭 전체 데이터 추출
(function() {
  const data = {};

  // 회사 기본 정보
  const companyName = document.querySelector('.org-top-card-summary__title, .artdeco-entity-lockup__title');
  data.company_name = companyName ? companyName.textContent.trim() : '';

  const subtitle = document.querySelector('.org-top-card-summary__subtitle, .artdeco-entity-lockup__subtitle');
  data.company_subtitle = subtitle ? subtitle.textContent.trim() : '';

  // 직원 수
  const empText = document.body.innerText.match(/(\d[\d,]*)\s*employees?\s*on\s*LinkedIn/i);
  data.linkedin_employees = empText ? parseInt(empText[1].replace(/,/g, '')) : null;

  // 모든 카드/위젯의 텍스트 수집
  const sections = document.querySelectorAll('.insight-card, .artdeco-card, [class*="module"], [class*="widget"]');
  data.sections = [];
  sections.forEach((s, i) => {
    const text = s.innerText.trim();
    if (text.length > 10 && text.length < 5000) {
      data.sections.push({
        index: i,
        text: text.substring(0, 2000)
      });
    }
  });

  return JSON.stringify(data);
})()
```

**대안: get_page_text로 전체 텍스트 추출 후 파싱**

Overview 탭의 텍스트를 `get_page_text`로 추출한 후 아래 패턴으로 파싱:

```python
import re

def parse_overview_text(text: str) -> dict:
    """Overview 탭 텍스트에서 구조화 데이터 추출"""
    data = {}

    # 직원 수
    m = re.search(r'(\d[\d,]*)\s*employees?\s*on\s*LinkedIn', text, re.I)
    data['linkedin_employees'] = int(m.group(1).replace(',', '')) if m else None

    # 성장률
    m = re.search(r'([+-]?\d+\.?\d*)%\s*(growth|increase|decrease)', text, re.I)
    data['growth_rate'] = float(m.group(1)) if m else None

    # Median tenure
    m = re.search(r'median\s*tenure[:\s]*(\d+\.?\d*)\s*(year|month)', text, re.I)
    if m:
        val = float(m.group(1))
        unit = m.group(2).lower()
        data['median_tenure_months'] = val * 12 if 'year' in unit else val

    # Hires / Departures
    m = re.search(r'(\d[\d,]*)\s*(?:new\s*)?hires?', text, re.I)
    data['total_hires'] = int(m.group(1).replace(',', '')) if m else None

    m = re.search(r'(\d[\d,]*)\s*departures?', text, re.I)
    data['total_departures'] = int(m.group(1).replace(',', '')) if m else None

    return data
```

### 2C. Talent Flow 탭 데이터 수집

Talent Flow 탭에서 수집할 데이터:

```
┌─────────────────────────────────────────────────────────┐
│ Talent Flow 탭 수집 항목                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. 트렌드 차트 데이터                                    │
│    [Hires + Departures 탭]                               │
│    - 월별 Hires 수 (시계열)                              │
│    - 월별 Departures 수 (시계열)                          │
│    [Employees 탭]                                        │
│    - 월별 총 직원 수 (시계열)                              │
│                                                         │
│ 2. 요약 수치                                             │
│    - Total Hires (예: 32)                                │
│    - Total Departures (예: 22)                           │
│    - Net change (예: +10)                                │
│                                                         │
│ 3. 인재 이동 상위 기업                                    │
│    - Companies with the most hires (입사 출처)           │
│    - Companies with the most departures (퇴사 행선지)    │
│                                                         │
│ 4. 인재 이동 전체 테이블 ★                               │
│    "From what companies is {Company}                     │
│     winning and losing talent?"                          │
│    - Company (전체 행)                                   │
│    - Departures 수                                       │
│    - Hires 수                                            │
│    - Ratio                                               │
│    - Net change                                          │
│                                                         │
│ 5. Detail 페이지 (각 회사 행 클릭 시) ★                  │
│    - 구체적인 인재 이동 프로필/직함 정보                    │
│    - 이동 시기                                           │
│    - 이동 방향 (입사/퇴사)                                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**수집 절차:**

```
Step 1 — Talent Flow 탭 클릭
  - "Talent flow" 탭 링크 클릭
  - 랜덤 딜레이: human_delay(2, 4)
  - 페이지 로딩 완료 대기

Step 2 — 트렌드 차트 및 요약 수치 수집
  - "How has this workforce trended over time?" 섹션
  - "Hires + Departures" 탭: 월별 데이터 추출
  - 요약: Total Hires, Departures, Net change
  - 상위 기업: most hires, most departures
  - 랜덤 딜레이: human_delay(1, 3)

Step 3 — "Employees" 서브탭 클릭 (있는 경우)
  - 월별 직원 수 시계열 추출
  - 랜덤 딜레이: human_delay(2, 4)

Step 4 — 인재 이동 전체 테이블 수집
  - "From what companies is {Company} winning and losing talent?" 테이블
  - 모든 행(Company, Departures, Hires, Ratio, Net change) 수집
  - 스크롤하여 모든 행 로드 (가상 스크롤 대응)
  - View by: "Last 12 months" 확인
  - 랜덤 딜레이: human_delay(1, 2) per scroll

Step 5 — Detail 팝업 수집 (각 회사 행 클릭) ★
  - 테이블의 각 회사 행 클릭 → **팝업/모달 오버레이**가 열림 (별도 페이지 아님)
  - 팝업에서 수집할 데이터:
    · 회사 기본 정보 (직원 수 범위, 설립 연도, 산업군 등)
    · 이동한 인원 수 및 방향
    · 직함/포지션 정보 (있는 경우)
  - 팝업 닫기 (X 버튼 또는 배경 클릭)로 테이블 복귀
  - 랜덤 딜레이: human_delay(2, 5) per detail
  - ⚠️ 행이 많으면 상위 10개사만 Detail 수집 (나머지는 요약만)

  **페이지네이션 처리:**
  - 테이블 하단에 **Page 1, 2, 3...** 버튼이 존재 (무한 스크롤 아님)
  - 각 페이지 전환 시 DOM이 갱신되므로 **ref_id가 변경됨**
  - 페이지 전환 후 반드시 `read_page`로 새 ref_id 확인 필요
  - 페이지당 약 10개 행 표시
```

**Talent Flow 데이터 추출 JavaScript:**

```javascript
// Talent Flow 요약 수치 + 트렌드 데이터 추출
(function() {
  const data = {};
  const text = document.body.innerText;

  // 요약 수치: Hires, Departures, Net change
  const hires = text.match(/(\d[\d,]*)\s*Hires/);
  const deps = text.match(/(\d[\d,]*)\s*Departures/);
  const net = text.match(/([+-]?\d[\d,]*)\s*Net\s*change/);

  data.total_hires = hires ? parseInt(hires[1].replace(/,/g, '')) : null;
  data.total_departures = deps ? parseInt(deps[1].replace(/,/g, '')) : null;
  data.net_change = net ? parseInt(net[1].replace(/[,+]/g, '')) : null;

  // 상위 입사 출처 기업
  data.top_hire_sources = [];
  const hiresSection = text.match(/COMPANIES WITH THE MOST HIRES([\s\S]*?)COMPANIES WITH THE MOST DEPARTURES/i);
  if (hiresSection) {
    const lines = hiresSection[1].trim().split('\n').filter(l => l.trim());
    lines.forEach(l => {
      const m = l.trim().match(/(.+?)\s+(\d+)$/);
      if (m) data.top_hire_sources.push({ company: m[1].trim(), count: parseInt(m[2]) });
    });
  }

  // 상위 퇴사 행선지 기업
  data.top_departure_destinations = [];
  const depsSection = text.match(/COMPANIES WITH THE MOST DEPARTURES([\s\S]*?)(?:From what|$)/i);
  if (depsSection) {
    const lines = depsSection[1].trim().split('\n').filter(l => l.trim());
    lines.forEach(l => {
      const m = l.trim().match(/(.+?)\s+(\d+)$/);
      if (m) data.top_departure_destinations.push({ company: m[1].trim(), count: parseInt(m[2]) });
    });
  }

  return JSON.stringify(data);
})()
```

**인재 이동 전체 테이블 추출 JavaScript:**

```javascript
// "From what companies" 테이블 전체 행 수집
(function() {
  const rows = [];
  // 테이블 행 셀렉터 (LinkedIn Talent Insights 구조)
  const tableRows = document.querySelectorAll('table tbody tr, [class*="talent-flow"] [class*="row"], [role="row"]');

  tableRows.forEach(row => {
    const cells = row.querySelectorAll('td, [role="cell"], [class*="cell"]');
    if (cells.length >= 4) {
      const companyEl = cells[0];
      const companyName = companyEl.textContent.trim();

      // 숫자 추출 헬퍼
      const getNum = (el) => {
        const t = el.textContent.trim();
        const n = t.match(/(-?\d+)/);
        return n ? parseInt(n[1]) : 0;
      };

      if (companyName && !companyName.includes('Company')) {  // 헤더 제외
        rows.push({
          company: companyName,
          departures: getNum(cells[1]),
          hires: getNum(cells[2]),
          ratio: cells[3] ? cells[3].textContent.trim() : '',
          net_change: cells[4] ? getNum(cells[4]) : 0
        });
      }
    }
  });

  return JSON.stringify(rows);
})()
```

**테이블 페이지네이션 처리:**

> 인재 이동 테이블은 **무한 스크롤이 아닌 페이지네이션** 방식.
> 하단에 "Page 1, 2, 3..." 버튼이 있으며, 페이지당 약 10개 행 표시.

```
페이지네이션 수집 절차:
1. 현재 페이지(기본 Page 1) 데이터 수집
2. read_page(tabId, filter="interactive")로 페이지 버튼 ref_id 확인
3. Page 2 버튼 클릭 → human_delay(2, 4)
4. ⚠️ DOM 갱신으로 기존 ref_id 무효화됨 → 다시 read_page 실행
5. 새 페이지 데이터 수집
6. 다음 페이지 반복 (마지막 페이지까지)

주의사항:
- 페이지 전환 시 ref_id가 완전히 변경되므로 이전 ref_id 재사용 금지
- 각 페이지에서 read_page를 다시 호출하여 새 ref_id 확보 필수
- 마지막 페이지 판별: "다음" 버튼 비활성 또는 페이지 번호 확인
```

### 2C-4. Detail 팝업 수집

인재 이동 테이블에서 각 회사 행을 클릭하면 **팝업/모달 오버레이**가 열립니다 (별도 페이지 이동 아님).

```
Step 1 — 행 클릭
  - read_page(tabId, filter="interactive")로 테이블 행의 ref_id 확인
  - 해당 행 클릭 (computer action: left_click)
  - 랜덤 딜레이: human_delay(2, 5)

Step 2 — 팝업 데이터 추출
  - read_page 또는 get_page_text로 팝업 내용 수집
  - 수집 항목:
    · 회사 기본 정보 (직원 수 범위, 설립 연도, 산업군)
    · 이동한 인원 수 및 방향
    · 직함/포지션 정보 (있는 경우)
  - 데이터는 `related_company_info` JSONB 컬럼에 저장

Step 3 — 팝업 닫기
  - X 버튼 또는 팝업 외부 영역 클릭으로 닫기
  - ⚠️ navigate("back") 사용 금지 — 팝업이므로 뒤로가기 불필요
  - 원래 테이블 상태 유지 확인
  - 랜덤 딜레이: human_delay(2, 4)

⚠️ 효율성 규칙:
  - 전체 행이 20개 이하: 모든 행 Detail 수집
  - 전체 행이 20개 초과: 상위 10개사 (이동 인원 많은 순) Detail만 수집
  - 나머지는 테이블 요약 데이터만 저장
  - Detail 없는 레코드에도 "related_company_info": null 필수 (배치 삽입 호환)
```

---

## Phase 3: Supabase 저장 설계

### 3A. 테이블 스키마 (PostgreSQL)

**`ti_overview` — 회사 Overview 스냅샷 (시계열)**

```sql
CREATE TABLE ti_overview (
  id                        BIGSERIAL PRIMARY KEY,
  snapshot_date             DATE NOT NULL,
  company                   TEXT NOT NULL,              -- 정규화된 회사명
  company_linkedin_name     TEXT,                       -- LinkedIn 표시 회사명
  linkedin_employees        INT,                        -- LinkedIn 기준 직원 수
  industry                  TEXT,                       -- 산업군
  headquarters              TEXT,                       -- 본사 위치
  employee_growth_6m        NUMERIC(5,2),               -- 6개월 성장률 (%)
  employee_growth_12m       NUMERIC(5,2),               -- 12개월 성장률 (%)
  median_tenure_months      NUMERIC(5,1),               -- 중간 재직 기간 (월)
  total_hires_12m           INT,                        -- 12개월 신규 채용
  total_departures_12m      INT,                        -- 12개월 퇴사
  net_headcount_change      INT,                        -- 순 인원 변화
  attrition_rate            NUMERIC(5,2),               -- 이탈률 (%)
  top_functions             JSONB,                      -- 상위 부서 [{"name":"Engineering","pct":27}, ...]
  fastest_growing_functions JSONB,                      -- 급성장 부서 [{"name":"HR","pct":133}, ...]
  top_skills                JSONB,                      -- 상위 스킬 [{"name":"JavaScript","count":18}, ...]
  fast_growing_skills       JSONB,                      -- 성장 스킬 [{"name":"TypeScript","pct":50}, ...]
  top_schools               JSONB,                      -- 상위 출신 학교
  top_fields_of_study       JSONB,                      -- 상위 전공 분야
  function_breakdown        JSONB,                      -- 부서별 분포 {"Engineering": 45, ...}
  seniority_breakdown       JSONB,                      -- 직급별 분포 {"Senior": 30, ...}
  raw_overview_text         TEXT,                       -- 원본 텍스트 (파싱 검증용)
  inserted_at               TIMESTAMPTZ DEFAULT NOW(),
  updated_at                TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (snapshot_date, company)
);

CREATE INDEX idx_ti_overview_company ON ti_overview (company, snapshot_date DESC);
CREATE INDEX idx_ti_overview_date    ON ti_overview (snapshot_date DESC);
```

**`ti_talent_flow_summary` — Talent Flow 요약 (시계열)**

```sql
CREATE TABLE ti_talent_flow_summary (
  id                      BIGSERIAL PRIMARY KEY,
  snapshot_date           DATE NOT NULL,
  company                 TEXT NOT NULL,
  period                  TEXT DEFAULT 'Last 12 months',  -- 조회 기간
  total_hires             INT,                            -- 총 입사자 수
  total_departures        INT,                            -- 총 퇴사자 수
  net_change              INT,                            -- 순 변화
  top_hire_sources        JSONB,                          -- 입사 출처 상위 [{company, count}, ...]
  top_departure_dests     JSONB,                          -- 퇴사 행선지 상위 [{company, count}, ...]
  flow_company_count      INT,                            -- 인재 이동 관련 회사 수
  flow_industry_count     INT,                            -- 인재 이동 관련 산업 수
  geography_data          JSONB,                          -- 지역별 인재 분포 데이터
  monthly_trend           JSONB,                          -- 월별 Hires/Departures [{month, hires, departures}, ...]
  monthly_employees       JSONB,                          -- 월별 직원 수 [{month, count}, ...]
  inserted_at             TIMESTAMPTZ DEFAULT NOW(),
  updated_at              TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (snapshot_date, company)
);

CREATE INDEX idx_ti_flow_summary_company ON ti_talent_flow_summary (company, snapshot_date DESC);
```

**`ti_talent_flow_detail` — 회사 간 인재 이동 상세 (시계열)**

```sql
CREATE TABLE ti_talent_flow_detail (
  id                    BIGSERIAL PRIMARY KEY,
  snapshot_date         DATE NOT NULL,
  company               TEXT NOT NULL,              -- 분석 대상 회사 (우리 고객사)
  related_company       TEXT NOT NULL,              -- 인재 이동 상대 회사
  departures            INT DEFAULT 0,             -- 대상→상대 이동 수 (퇴사)
  hires                 INT DEFAULT 0,             -- 상대→대상 이동 수 (입사)
  ratio                 TEXT,                       -- 비율 표시
  net_change            INT DEFAULT 0,             -- 순 변화 (hires - departures 관점)
  related_company_info  JSONB,                      -- Detail 팝업에서 수집한 회사 정보
                                                    -- {"employees":"51-200","founded":2020,"industry":"..."}
  detail_profiles       JSONB,                      -- Detail 클릭 시 수집한 프로필 정보
                                                    -- [{title, move_date, direction}, ...]
  inserted_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE (snapshot_date, company, related_company)
);

CREATE INDEX idx_ti_flow_detail_company ON ti_talent_flow_detail (company, snapshot_date DESC);
CREATE INDEX idx_ti_flow_detail_related ON ti_talent_flow_detail (related_company);
```

**`ti_company_mapping` — 회사명 ↔ LinkedIn ID 매핑 (영구)**

```sql
CREATE TABLE ti_company_mapping (
  id                    BIGSERIAL PRIMARY KEY,
  company               TEXT NOT NULL UNIQUE,      -- 정규화된 회사명 (company_weekly 기준)
  linkedin_company_id   TEXT,                       -- LinkedIn encoded_id (URL에서 추출)
  linkedin_company_name TEXT,                       -- LinkedIn 표시 회사명 (영문)
  linkedin_url          TEXT,                       -- 전체 Insights URL (직접 접속용)
  search_query_used     TEXT,                       -- 매칭 시 사용한 검색어
  status                TEXT DEFAULT 'unverified',  -- unverified/verified/not_found/ambiguous
  verified_at           TIMESTAMPTZ,
  last_used_at          TIMESTAMPTZ,
  notes                 TEXT,                       -- 매칭 실패 사유 등 메모
  inserted_at           TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ti_mapping_status ON ti_company_mapping (status);
CREATE INDEX idx_ti_mapping_linkedin_id ON ti_company_mapping (linkedin_company_id);
```

> **매핑 활용 우선순위:**
> 1. `status = 'verified'` + `linkedin_url` 있음 → URL 직접 접속 (검색 스킵)
> 2. `status = 'verified'` + `linkedin_company_name` 있음 → 영문명으로 검색
> 3. `status = 'unverified'` 또는 미등록 → 한글 회사명으로 검색 후 매핑 저장
> 4. `status = 'not_found'` → 스킵 (7일 후 재시도)

**`ti_collection_log` — 수집 세션 로그 (진행률 추적)**

```sql
CREATE TABLE ti_collection_log (
  id                      BIGSERIAL PRIMARY KEY,
  session_id              TEXT NOT NULL,               -- 수집 세션 고유 ID (UUID)
  snapshot_date           DATE NOT NULL,
  company                 TEXT NOT NULL,
  phase                   TEXT NOT NULL,               -- 'overview' / 'flow_summary' / 'flow_detail'
  status                  TEXT DEFAULT 'pending',      -- pending/in_progress/success/failed/skipped
  error_message           TEXT,
  companies_processed     INT DEFAULT 0,               -- 현재 세션에서 처리한 회사 수 (딜레이 계산용)
  page_load_time_ms       INT,                         -- 페이지 로드 시간 (적응형 딜레이 판단)
  started_at              TIMESTAMPTZ,
  completed_at            TIMESTAMPTZ,
  inserted_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ti_log_session ON ti_collection_log (session_id, company);
CREATE INDEX idx_ti_log_status ON ti_collection_log (status, snapshot_date DESC);
```

> **용도:**
> - 중간 실패 시 재개: `status != 'success'`인 회사부터 이어서 수집
> - 10개사 쿨다운 판단: `companies_processed` 카운터로 정확한 타이밍
> - 적응형 딜레이: `page_load_time_ms > 8000`이면 후속 딜레이 1.5배
> - 수집 완료 검증: 3개 phase 모두 `success`여야 해당 회사 완료로 판정

> **Supabase REST API 배치 삽입 주의사항:**
> 여러 레코드를 한번에 INSERT할 때, 모든 객체의 키가 동일해야 함 (PGRST102 에러 방지).
> `related_company_info`가 없는 레코드에도 `"related_company_info": null`을 명시적으로 포함해야 한다.

### 3A-1. 데이터 검증 (저장 전 필수)

> **빈 데이터나 비정상 값을 저장하면 시계열 분석이 오염됩니다.**
> 저장 전 반드시 아래 검증을 통과해야 합니다.

```python
def validate_overview(data: dict) -> tuple:
    """Overview 데이터 검증 → (is_valid, errors)"""
    errors = []

    if not data.get('linkedin_employees') and not data.get('raw_text'):
        errors.append("직원 수와 원본 텍스트 모두 없음 — 페이지 로드 실패 의심")

    if data.get('linkedin_employees') and data['linkedin_employees'] > 500000:
        errors.append(f"직원 수 비정상: {data['linkedin_employees']} (50만 초과)")

    growth = data.get('employee_growth_12m')
    if growth and (growth > 500 or growth < -90):
        errors.append(f"성장률 비정상: {growth}% (범위: -90% ~ +500%)")

    return (len(errors) == 0, errors)


def validate_flow_details(rows: list) -> tuple:
    """Talent Flow 상세 데이터 검증"""
    errors = []

    if not rows:
        errors.append("인재 이동 데이터가 비어있음 — Talent Flow 탭 파싱 실패 의심")

    for r in rows:
        if not r.get('company'):
            errors.append("관련 회사명이 비어있는 행 존재")
            break

    return (len(errors) == 0, errors)
```

**검증 실패 시 처리:**
- `ti_collection_log`에 `status='failed'`, `error_message`에 검증 실패 사유 기록
- 해당 회사 데이터는 저장하지 않고 스킵
- 다음 회사로 이동 (세션 중단하지 않음)

### 3B. Supabase 저장 코드

```python
import os
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_KEY = os.environ['SUPABASE_KEY']  # service_role key
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_ti_overview(company: str, overview_data: dict, snapshot_date: str):
    """Overview 데이터 저장"""
    row = {
        "snapshot_date":             snapshot_date,
        "company":                   company,
        "company_linkedin_name":     overview_data.get('company_linkedin_name', ''),
        "linkedin_employees":        overview_data.get('linkedin_employees'),
        "industry":                  overview_data.get('industry', ''),
        "headquarters":              overview_data.get('headquarters', ''),
        "employee_growth_6m":        overview_data.get('employee_growth_6m'),
        "employee_growth_12m":       overview_data.get('employee_growth_12m'),
        "median_tenure_months":      overview_data.get('median_tenure_months'),
        "total_hires_12m":           overview_data.get('total_hires'),
        "total_departures_12m":      overview_data.get('total_departures'),
        "net_headcount_change":      overview_data.get('net_change'),
        "attrition_rate":            overview_data.get('attrition_rate'),
        "top_functions":             overview_data.get('top_functions', []),
        "fastest_growing_functions": overview_data.get('fastest_growing_functions', []),
        "top_skills":                overview_data.get('top_skills', []),
        "fast_growing_skills":       overview_data.get('fast_growing_skills', []),
        "top_schools":               overview_data.get('top_schools', []),
        "top_fields_of_study":       overview_data.get('top_fields_of_study', []),
        "function_breakdown":        overview_data.get('function_breakdown', {}),
        "seniority_breakdown":       overview_data.get('seniority_breakdown', {}),
        "raw_overview_text":         overview_data.get('raw_text', '')[:5000]
    }
    supabase.table("ti_overview").upsert(row).execute()


def save_ti_flow_summary(company: str, flow_data: dict, snapshot_date: str):
    """Talent Flow 요약 저장"""
    row = {
        "snapshot_date":         snapshot_date,
        "company":               company,
        "period":                flow_data.get('period', 'Last 12 months'),
        "total_hires":           flow_data.get('total_hires'),
        "total_departures":      flow_data.get('total_departures'),
        "net_change":            flow_data.get('net_change'),
        "top_hire_sources":      flow_data.get('top_hire_sources', []),
        "top_departure_dests":   flow_data.get('top_departure_destinations', []),
        "flow_company_count":    flow_data.get('flow_company_count'),
        "flow_industry_count":   flow_data.get('flow_industry_count'),
        "geography_data":        flow_data.get('geography_data'),
        "monthly_trend":         flow_data.get('monthly_trend', []),
        "monthly_employees":     flow_data.get('monthly_employees', [])
    }
    supabase.table("ti_talent_flow_summary").upsert(row).execute()


def save_ti_flow_details(company: str, flow_rows: list, snapshot_date: str):
    """인재 이동 상세 테이블 저장"""
    rows = [{
        "snapshot_date":       snapshot_date,
        "company":             company,
        "related_company":     r['company'],
        "departures":          r.get('departures', 0),
        "hires":               r.get('hires', 0),
        "ratio":               r.get('ratio', ''),
        "net_change":          r.get('net_change', 0),
        "related_company_info": r.get('related_company_info', None),  # ⚠️ null 필수 (배치 호환)
        "detail_profiles":     r.get('detail_profiles', None)
    } for r in flow_rows]

    # ⚠️ 모든 객체의 키가 동일해야 Supabase REST API 배치 삽입 성공 (PGRST102)
    supabase.table("ti_talent_flow_detail").upsert(rows).execute()
```

### 3C. 시계열 트렌드 조회 SQL

```sql
-- 특정 회사의 직원 수 변화 추이 (최근 12주)
SELECT
  snapshot_date,
  company,
  linkedin_employees,
  total_hires_12m,
  total_departures_12m,
  net_headcount_change,
  employee_growth_12m,
  linkedin_employees - LAG(linkedin_employees) OVER (ORDER BY snapshot_date) AS wow_employee_change
FROM ti_overview
WHERE company = '번개장터'
ORDER BY snapshot_date DESC
LIMIT 12;
```

```sql
-- 특정 회사의 인재 유출입 상위 기업 (최신)
SELECT
  related_company,
  departures,
  hires,
  net_change,
  detail_profiles
FROM ti_talent_flow_detail
WHERE company = '번개장터'
  AND snapshot_date = (SELECT MAX(snapshot_date) FROM ti_talent_flow_detail WHERE company = '번개장터')
ORDER BY ABS(net_change) DESC;
```

```sql
-- 전체 타겟 회사 최신 현황 대시보드
SELECT
  o.company,
  o.linkedin_employees,
  o.employee_growth_12m,
  o.net_headcount_change,
  f.total_hires,
  f.total_departures,
  f.flow_company_count,
  cw.opp_score
FROM ti_overview o
LEFT JOIN ti_talent_flow_summary f
  ON o.company = f.company AND o.snapshot_date = f.snapshot_date
LEFT JOIN company_weekly cw
  ON o.company = cw.company
  AND cw.snapshot_date = (SELECT MAX(snapshot_date) FROM company_weekly)
WHERE o.snapshot_date = (SELECT MAX(snapshot_date) FROM ti_overview)
ORDER BY cw.opp_score DESC NULLS LAST;
```

---

## Phase 4: 리포팅

### 브리핑 출력 형식

```
🔍 Talent Insight 분석 (YYYY-MM-DD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 고객사 인재 현황 요약 ({N}개사 수집)

 ┌──────────────┬───────┬────────┬────────┬────────┬────────┬────────┐
 │ 회사          │ 직원수 │ 성장률  │ 입사   │ 퇴사   │ Net    │ Tenure │
 ├──────────────┼───────┼────────┼────────┼────────┼────────┼────────┤
 │ {회사A}       │  {N}  │ +{X}%  │  {N}   │  {N}   │ +{N}   │ {N}년  │
 │ {회사B}       │  {N}  │ -{X}%  │  {N}   │  {N}   │ -{N}   │ {N}년  │
 │ {회사C}       │  {N}  │ +{X}%  │  {N}   │  {N}   │ +{N}   │ {N}년  │
 │ ...          │       │        │        │        │        │        │
 └──────────────┴───────┴────────┴────────┴────────┴────────┴────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 인재 흐름 하이라이트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 빠르게 성장 중 (성장률 10%+):
  {회사A} (+25%, 직원 {N}→{N}명)
  {회사B} (+15%, 직원 {N}→{N}명)

📉 인재 유출 심각 (Net change 마이너스):
  {회사C} (입사 {N} vs 퇴사 {N}, Net -{N})
  {회사D} (입사 {N} vs 퇴사 {N}, Net -{N})

🔀 주요 인재 이동 경로:
  {회사A} ← {출처기업1}({N}명), {출처기업2}({N}명)
  {회사B} → {행선지1}({N}명), {행선지2}({N}명)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 영업 인사이트
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 적극 어프로치 대상 (성장 + 채용 활발):
  {회사A}: 직원 {N}명, 성장률 +{X}%, 채용 {N}건 진행 중 (OppScore {N})
  → 인재 유입처: {기업1}, {기업2} — 경쟁사 동향 파악 가능

⚠️ 이탈 리스크 고객사 (인재 유출 심각):
  {회사C}: 최근 12개월 퇴사 {N}명, 주요 행선지 {기업1}, {기업2}
  → 리텐션 컨설팅 제안 또는 대체 인력 서치 기회

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💾 저장 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Supabase ti_overview: {N}개사 upsert ✅
Supabase ti_talent_flow_summary: {N}개사 upsert ✅
Supabase ti_talent_flow_detail: {N}건 upsert ✅
```

### 단일 회사 상세 리포트

```
🏢 {회사명} Talent Insight Detail (YYYY-MM-DD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 기본 정보
  회사명: {회사명} ({LinkedIn 표시명})
  산업: {산업군}
  직원 수: {N}명 (LinkedIn 기준)
  성장률: {+/-X}% (12개월)
  중간 재직기간: {N}년 {N}개월

📊 채용/이직 현황 (최근 12개월)
  신규 채용: {N}명
  퇴사: {N}명
  순 변화: {+/-N}명

🔄 인재 흐름 상세 (총 {N}개사 관련)

  [입사 출처 Top 5]
   1. {기업A} → {회사명}: {N}명
   2. {기업B} → {회사명}: {N}명
   ...

  [퇴사 행선지 Top 5]
   1. {회사명} → {기업C}: {N}명
   2. {회사명} → {기업D}: {N}명
   ...

  [전체 인재 이동 테이블]
  ┌──────────────────┬──────┬──────┬───────┬──────────┐
  │ 관련 회사         │ 퇴사  │ 입사 │ 비율  │ Net     │
  ├──────────────────┼──────┼──────┼───────┼──────────┤
  │ Toss Payments    │  2   │  1   │  -2   │   -1     │
  │ MUSINSA 무신사    │  2   │  0   │  -2   │   -2     │
  │ 스펙터 Specter    │  0   │  1   │  +1   │   +1     │
  │ ...              │      │      │       │          │
  └──────────────────┴──────┴──────┴───────┴──────────┘
```

---

## 주의사항 및 운영 가이드

### Rate Limiting (최중요)

1. **랜덤 딜레이 필수**: 모든 액션 사이에 `human_delay()` 삽입. 고정 간격 금지.
2. **연속 10개사 후 장시간 대기**: 10개사 처리마다 30~60초 쉬기.
3. **세션당 최대 30개사**: 한 세션에서 30개사 이상 수집 시 LinkedIn 감지 위험.
4. **시간대 분산**: 가능하면 업무 시간(오전 9시~오후 6시 KST)에 실행하여 자연스러운 사용 패턴 유지.

### 회사명 매칭

5. **회사명 정규화**: Supabase의 `company_weekly.company`와 LinkedIn의 회사명이 다를 수 있음.
   - 예: "번개장터" ↔ "Bungaejangter Inc."
   - Company 필드 입력 시 자동완성 드롭다운에서 가장 관련도 높은 결과 선택.
   - 매칭 실패 시 스킵하고 다음 회사로 이동.

6. **LinkedIn 회사명 저장**: `company_linkedin_name` 컬럼에 LinkedIn 표시 회사명을 별도 저장하여 이후 매칭에 활용.

### Talent Insights 접근 권한

7. **Premium 필수**: LinkedIn Talent Insights는 유료 기능. 접근 불가 시 사용자에게 안내.
8. **데이터 한도**: Talent Insights는 API가 아닌 웹 UI 기반이므로 수집 속도에 한계가 있음.

### Supabase 관련

9. **service_role key 사용**: INSERT/UPSERT에는 anon key가 아닌 service_role key 필요.
10. **jobmarket과 동일 프로젝트**: `positions`, `weekly_snapshot`, `company_weekly` 테이블과 같은 Supabase 프로젝트 사용.
11. **JSONB 컬럼**: `function_breakdown`, `seniority_breakdown`, `detail_profiles` 등은 JSONB로 유연하게 저장.

### 시계열 분석

12. **주간 수집 권장**: jobmarket 스킬과 같은 주기로 실행하여 비교 분석 가능.
13. **첫 4주 기준선**: 누적 데이터 4주 미만 시 WoW 변화 해석에 주의.
14. **LinkedIn 데이터 특성**: LinkedIn 직원 수는 실제와 차이가 있을 수 있음 (등록 기반). 절대값보다 **변화 추이**에 집중.

---

## 데이터 저장 경로

| 저장소 | 위치 | 내용 |
|--------|------|------|
| **Supabase (기본)** | `ti_overview` | 회사 Overview 스냅샷 (시계열) |
| **Supabase (기본)** | `ti_talent_flow_summary` | Talent Flow 요약 (시계열) |
| **Supabase (기본)** | `ti_talent_flow_detail` | 회사 간 인재 이동 상세 |
| **Supabase (신규)** | `ti_company_mapping` | 회사명 ↔ LinkedIn ID 매핑 |
| **Supabase (신규)** | `ti_collection_log` | 수집 세션 로그/진행률 |
| **스킬 정의** | `skill/talent-insight/skill.md` | 이 파일 |

---

## 트리거별 실행 범위

| 트리거 | Phase | 비고 |
|--------|-------|------|
| "talent insight 돌려줘" | 0→1→2→3→4 | 전체 실행 (Supabase 상위 30개사) |
| "번개장터 인사이트" | 0→2(해당사만)→3→4 | 단일 회사 |
| "인재 흐름 분석해줘" | 0→1→2C(Flow만)→3→4 | Talent Flow만 수집 |
| "고객사 현황 대시보드" | Supabase 조회→4 | 스크래핑 없이 DB 조회만 |
| "인재 이동 트렌드" | Supabase SQL 조회 | 시계열 분석 |
| 위클리 연동 | Supabase 조회→Notion 업데이트 | weekly/skill.md에서 호출 |

---

## jobmarket 스킬과의 연동

### 통합 영업 인텔리전스 쿼리

```sql
-- jobmarket OppScore + Talent Insight 통합 뷰
SELECT
  cw.company,
  cw.opp_score,
  cw.total_positions AS active_openings,
  cw.weeks_consecutive,
  o.linkedin_employees,
  o.employee_growth_12m,
  o.net_headcount_change,
  f.total_hires AS ti_hires_12m,
  f.total_departures AS ti_departures_12m,
  -- 채용 강도 지수: 현재 공고 수 / 직원 수 × 100
  ROUND(cw.total_positions::numeric / NULLIF(o.linkedin_employees, 0) * 100, 2) AS hiring_intensity,
  -- 이탈률: 퇴사 / 직원 × 100
  ROUND(f.total_departures::numeric / NULLIF(o.linkedin_employees, 0) * 100, 2) AS attrition_rate
FROM company_weekly cw
LEFT JOIN ti_overview o
  ON cw.company = o.company
  AND o.snapshot_date = (SELECT MAX(snapshot_date) FROM ti_overview)
LEFT JOIN ti_talent_flow_summary f
  ON cw.company = f.company
  AND f.snapshot_date = (SELECT MAX(snapshot_date) FROM ti_talent_flow_summary)
WHERE cw.snapshot_date = (SELECT MAX(snapshot_date) FROM company_weekly)
  AND cw.opp_score >= 55
ORDER BY cw.opp_score DESC;
```

### 채용 강도 + 이탈률 해석

| 채용 강도 (%) | 이탈률 (%) | 영업 시그널 |
|--------------|-----------|------------|
| 높음 (>5%) | 높음 (>20%) | 인재 유출 심각 + 대량 채용 = **최우선 어프로치** |
| 높음 (>5%) | 낮음 (<10%) | 성장에 의한 채용 = 프리미엄 포지셔닝 가능 |
| 낮음 (<2%) | 높음 (>20%) | 인재 유출 중 but 채용 미비 = 리텐션 컨설팅 제안 |
| 낮음 (<2%) | 낮음 (<10%) | 안정 상태 = 모니터링 유지 |
