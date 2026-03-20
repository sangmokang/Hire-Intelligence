# VXMI Dashboard Design Spec
> PRD 보완 문서 — S/D 매트릭스 대시보드 6개 뷰 설계 근거 및 인터랙션 스펙
> Harness feature_list.json P2–P5 구간 구현 참조 문서

---

## 개요

본 문서는 VXMI(ValueConnect Market Intelligence) 대시보드의 6개 핵심 뷰에 대한 설계 결정, 차트 선택 근거, 데이터 구조, 인터랙션 스펙을 정의합니다. Coding Agent는 이 문서를 기준으로 각 뷰를 구현합니다.

---

## 전체 대시보드 구조

```
/dashboard
  ├── SDMatrix          (S/D 매트릭스)
  ├── TopCompanies      (Top 20 채용 볼륨 — 주간 스냅샷)
  ├── CompanyTimeline   (시계열 기업 채용 인텔리전스) ← NEW
  ├── HiringTrends      (채용 트렌드)
  ├── ResumeMatch       (이력서 매칭)
  └── CompanyAnalysis   (기업 분석)
```

탭 네비게이션 기반. 각 뷰는 독립 컴포넌트로 lazy-load.

---

## View 1: S/D 매트릭스 (SDMatrix)

### 차트 타입
**Bubble Chart** (Chart.js 또는 Recharts ScatterChart + custom bubble)

### 선택 근거
- X축(수요) · Y축(공급) · 버블 크기(OTW%) → 3개 변수를 단일 좌표계에 표현
- 우하단 "기회지대" 사분면이 즉각적으로 시각화됨
- 14개 세그먼트 모두 동시에 비교 가능

### 축 정의
| 축 | 의미 | 데이터 소스 |
|---|---|---|
| X | 채용 수요 (주간 공고 수) | Wanted + LinkedIn + Saramin + JobKorea 합산 |
| Y | 인재 공급 (LinkedIn Recruiter 풀 사이즈) | LinkedIn Recruiter RPS |
| 버블 크기 | OTW% (Open to Work 비율) | LinkedIn Recruiter RPS |

### 사분면 기준선
```
X 기준선: 1,400 (주간 공고 수)
Y 기준선: 10,500 (인재 풀 사이즈)
```

| 사분면 | 위치 | 의미 |
|---|---|---|
| 기회지대 | 우하단 (고수요·저공급) | 영업 타겟 우선순위 1순위 |
| 경쟁 시장 | 우상단 (고수요·고공급) | 표준 서치 |
| 과잉 공급 | 좌상단 (저수요·고공급) | 후보자 시장 우위 |
| 틈새 시장 | 좌하단 (저수요·저공급) | 전문 서치 가능 |

### 14개 세그먼트 기준 데이터
```typescript
// /src/data/segments.ts
export const SEGMENTS = [
  { id: 'sw',    name: 'SW엔지니어링',  demand: 2840, supply: 18500, otwPct: 15, color: '#378ADD' },
  { id: 'data',  name: 'Data/AI',      demand: 1620, supply: 8200,  otwPct: 22, color: '#1D9E75' },
  { id: 'sales', name: '영업',          demand: 1240, supply: 15600, otwPct: 8,  color: '#E24B4A' },
  { id: 'prod',  name: 'Product',      demand: 890,  supply: 6100,  otwPct: 19, color: '#D4537E' },
  { id: 'ops',   name: '운영',          demand: 940,  supply: 11200, otwPct: 11, color: '#888780' },
  { id: 'mfg',   name: '제조',          demand: 1180, supply: 13600, otwPct: 9,  color: '#BA7517' },
  { id: 'mktg',  name: '마케팅',        demand: 760,  supply: 12400, otwPct: 13, color: '#7F77DD' },
  { id: 'fin',   name: '재무',          demand: 580,  supply: 9800,  otwPct: 10, color: '#5DCAA5' },
  { id: 'hr',    name: 'HR',           demand: 420,  supply: 7200,  otwPct: 14, color: '#F0997B' },
  { id: 'ux',    name: 'UX/UI',        demand: 680,  supply: 4800,  otwPct: 28, color: '#D85A30' },
  { id: 'legal', name: '법무',          demand: 280,  supply: 3200,  otwPct: 17, color: '#97C459' },
  { id: 'scm',   name: '물류SCM',       demand: 560,  supply: 8900,  otwPct: 12, color: '#FAC775' },
  { id: 'rd',    name: '연구개발',       demand: 840,  supply: 7400,  otwPct: 16, color: '#93B1EB' },
  { id: 'med',   name: '의료헬스케어',   demand: 720,  supply: 5600,  otwPct: 24, color: '#ED93B1' },
]
```

### S/D Ratio 기회지대 (ratio ≤ 0.20)
```
UX/UI:         0.14  ★ 최고 기회
SW엔지니어링:  0.15
Product:       0.15
의료헬스케어:  0.13
Data/AI:       0.20
```

### 인터랙션
- **버블 클릭** → 하단 드릴다운 패널 오픈 (해당 세그먼트 Top 채용 기업 + 포지션)
- **범례 클릭** → 동일 드릴다운 오픈
- **드릴다운 데이터 구조:**
```typescript
interface DrilldownItem {
  company: string
  position: string
  count: number
}
// Supabase: SELECT company, position_title, count FROM job_postings
// WHERE segment_id = $1 AND week = current_week ORDER BY count DESC LIMIT 5
```

### Summary Metrics (헤더 카드 4개)
| 메트릭 | 계산 |
|---|---|
| 전체 채용 공고 | SUM(demand) across all segments |
| 기회지대 세그먼트 수 | COUNT WHERE sd_ratio ≤ 0.20 |
| 평균 S/D Ratio | AVG(demand/supply) |
| 최고 기회 세그먼트 | MIN(sd_ratio).name |

---

## View 2: Top 20 채용 볼륨 (TopCompanies)

### 차트 타입
**Custom Horizontal Bar Ranking List** (CSS-based, not Chart.js)

### 선택 근거
- 순위 + 기업명 + 세그먼트 + 볼륨을 한 행에서 스캔
- Chart.js 수평 바 차트보다 인터랙션(행 펼침) 구현이 자유로움
- 세그먼트 색상 배지 자연스럽게 삽입 가능

### 데이터 구조
```typescript
interface CompanyRankItem {
  rank: number
  company: string
  segment: string
  weeklyCount: number
  positions: string[]   // 대표 포지션 태그 (최대 4개)
  weekOverWeekChange: number  // % 변화율
}
// Supabase: SELECT company, segment, SUM(count) as total, array_agg(DISTINCT position_title)
// FROM job_postings WHERE week = current_week
// GROUP BY company, segment ORDER BY total DESC LIMIT 20
```

### 인터랙션
- **행 클릭** → 포지션 태그 accordion 펼침/닫힘
- **세그먼트 필터** → 특정 세그먼트만 필터링 (선택사항 P3+)

---

## View 3: 채용 트렌드 (HiringTrends)

### 차트 타입
**Multi-line Chart** (Chart.js Line, 또는 Recharts LineChart)

### 선택 근거
- 시계열 비교는 라인 차트가 최적
- 5개 세그먼트 동시 표시 후 토글로 혼잡도 조절
- 데이터 포인트 클릭 드릴다운으로 "왜 그 주에 피크?"를 즉시 확인

### 기간 및 데이터
```
기본 표시: 최근 12주 (rolling window)
X축: 주차 레이블 (MM/DD 형식)
Y축: 해당 주 공고 수
```

```typescript
// 트래킹 세그먼트 (기본 5개, 확장 가능)
const DEFAULT_TREND_SEGMENTS = ['sw', 'data', 'sales', 'prod', 'mfg']

interface TrendDataPoint {
  week: string       // 'YYYY-WW' ISO format
  weekLabel: string  // 'MM/DD' display
  segmentId: string
  count: number
}
// Supabase: SELECT week, segment_id, SUM(count)
// FROM job_postings WHERE week >= (current - 12 weeks)
// GROUP BY week, segment_id ORDER BY week ASC
```

### 인터랙션
- **범례 토글 버튼** → 세그먼트별 라인 show/hide (Chart.js dataset.hidden)
- **데이터 포인트 클릭** → 해당 주차·세그먼트의 채용 기업 드릴다운
- **드릴다운 구조**: `{ week, segmentId } → CompanyRankItem[]`

---

## View 4: 이력서 매칭 (ResumeMatch)

### UI 패턴
**Text Input → Match Card Grid** (Chart 없음, 순수 UI 컴포넌트)

### 매칭 로직 (MVP)
```typescript
// MVP: 키워드 기반 매칭 (클라이언트사이드)
// P5+: Anthropic API embedding 기반 시맨틱 매칭
function matchResume(resumeText: string): MatchResult[] {
  const keywords = extractKeywords(resumeText)  // tokenize + stopword removal
  return COMPANY_DB
    .map(company => ({
      ...company,
      score: calculateMatchScore(keywords, company.requiredSkills)
    }))
    .filter(r => r.score > 60)
    .sort((a, b) => b.score - a.score)
    .slice(0, 6)
}
```

### Match Card 데이터 구조
```typescript
interface MatchResult {
  company: string
  score: number        // 0-100
  segment: string
  matchReason: string  // 1-2문장 한국어 설명
  matchedSkills: string[]
  activePostings: number
}
```

### 향후 확장 (P6+)
- Anthropic API (`claude-sonnet-4-20250514`) 호출로 시맨틱 매칭
- Supabase `ops` 스키마의 후보자 DB와 조인하여 역매칭 (포지션→후보자)

---

## View 5: 기업 분석 (CompanyAnalysis)

### UI 패턴
**Quick-select Buttons + Free Input → Two-Panel Card Grid** (Chart 없음)

### 2-Panel 구조
```
┌─────────────────────────┬─────────────────────────┐
│  인재 밀도 지수          │  채용 파워 지수           │
│  (Talent Density Index) │  (Hiring Power Index)    │
│                         │                          │
│  종합 스코어 /100        │  종합 스코어 /100         │
│  ├ 기술다양성            │  활성 포지션 수           │
│  ├ 시니어비율            │  12주 스파크 바 차트       │
│  ├ 평균재직기간           │                          │
│  └ 내부OTW%             │                          │
└─────────────────────────┴─────────────────────────┘
```

### 데이터 구조
```typescript
interface CompanyProfile {
  name: string
  talentDensity: {
    overall: number
    techDiversity: number    // 기술 스택 다양성
    seniorRatio: number      // 시니어(7년+) 비율
    avgTenure: string        // 평균 재직 기간 (e.g. '2.1년')
    internalOtwPct: number   // 내부 OTW 비율
  }
  hiringPower: {
    overall: number
    activePostings: number
    weeklyTrend: number[]    // 12주 히스토리 (스파크 바용)
  }
}
// Supabase JOIN:
// ops.companies (기업 정보) + pulse.job_postings (채용 수요)
// + pulse.talent_pool (공급/OTW) WHERE company = $1
```

### 기본 수록 기업 (MVP)
토스, 카카오, 네이버, 삼성전자, 쿠팡, LG전자, 현대자동차, 배달의민족

---

## Supabase 스키마 매핑

```sql
-- pulse 스키마 (VXMI 전용)
pulse.job_postings        -- 주간 공고 수 (세그먼트 × 기업 × 플랫폼)
pulse.talent_pool         -- 인재 풀 사이즈 + OTW 수 (세그먼트별)
pulse.weekly_snapshots    -- S/D ratio 주간 스냅샷 (52주 보존)

-- ops 스키마 (valueconnect-ops 공용)
ops.companies             -- 기업 마스터 데이터
ops.positions             -- 포지션 마스터

-- Cross-schema JOIN 예시 (단일 Supabase 프로젝트 필수 이유)
SELECT
  p.company_id,
  c.name,
  c.segment,
  SUM(p.count) as weekly_demand,
  t.pool_size,
  t.otw_count,
  ROUND(SUM(p.count)::numeric / t.pool_size, 3) as sd_ratio
FROM pulse.job_postings p
JOIN ops.companies c ON p.company_id = c.id
JOIN pulse.talent_pool t ON t.segment_id = c.segment_id AND t.week = p.week
WHERE p.week = $1
GROUP BY p.company_id, c.name, c.segment, t.pool_size, t.otw_count
ORDER BY weekly_demand DESC;
```

---

## View 3: 시계열 기업 채용 인텔리전스 (CompanyTimeline) ← NEW

### 목적
"어떤 회사가 지금 가장 많이 채용 중인가?"를 단순 주간 스냅샷이 아닌 **시계열 누적 + 키워드 필터** 관점에서 분석하는 영업 인텔리전스 뷰.

### 세 가지 조회 모드

| 모드 | 설명 | 주요 질문 |
|---|---|---|
| **Mode A** 총 채용 규모 | 기간 내 채용 공고 합산 기준 Top N | "지난 12주 가장 많이 뽑은 회사는?" |
| **Mode B** 단일 키워드 | 특정 직무/스킬 키워드 포함 공고 기준 Top N | "'Python' 포함 공고 가장 많은 회사는?" |
| **Mode C** 복합 키워드 | AND/OR 조합 키워드 기준 Top N | "'Python AND MLOps AND AWS' 모두 채용 중인 회사는?" |

Top N 범위: 20 / 50 / 100 (사용자 선택)

---

### UI 레이아웃

```
┌──────────────────────────────────────────────────────┐
│  [Mode A: 총 채용 규모] [Mode B: 키워드] [Mode C: 복합]  │
│                                                      │
│  기간: [4주 ▼]  Top: [20 ▼]  세그먼트: [전체 ▼]         │
│                                                      │
│  Mode B/C 시: ┌──────────────────────────────────┐   │
│               │ 키워드 입력 (엔터로 추가)            │   │
│               │ [Python ×] [MLOps ×] [AWS ×]      │   │
│               │ 연산자: (● AND  ○ OR)              │   │
│               └──────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  시계열 라인 차트 (Top 5 기업 / 나머지 그룹화)    │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  순위  기업명  세그먼트  [주간 스파크바]  총계  변화 │ │
│  │  1     삼성전자  제조   ▁▂▃▄▅▆▇  248   +2.4%  │ │
│  │  ...                                            │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

---

### Mode A: 총 채용 규모

```typescript
interface TotalVolumeQuery {
  weeks: 4 | 8 | 12 | 26 | 52   // 조회 기간
  topN: 20 | 50 | 100
  segmentId?: string              // 세그먼트 필터 (optional)
}

// Supabase 쿼리
// SELECT c.name, c.segment, SUM(p.count) as total,
//        array_agg(p.count ORDER BY p.week) as weekly_series,
//        ROUND((last_week_count - prev_week_count) / prev_week_count * 100, 1) as wow_change
// FROM pulse.job_postings p
// JOIN ops.companies c ON p.company_id = c.id
// WHERE p.week >= (current_week - $weeks)
//   AND ($segmentId IS NULL OR c.segment_id = $segmentId)
// GROUP BY c.id, c.name, c.segment
// ORDER BY total DESC
// LIMIT $topN
```

---

### Mode B: 단일 키워드

```typescript
interface KeywordQuery {
  keyword: string                 // 예: "Python", "React", "영업 관리"
  weeks: 4 | 8 | 12 | 26 | 52
  topN: 20 | 50 | 100
  segmentId?: string
}

// Supabase 쿼리 (position_title 또는 skills 컬럼 full-text 검색)
// SELECT c.name, c.segment, SUM(p.count) as keyword_count,
//        array_agg(p.count ORDER BY p.week) as weekly_series
// FROM pulse.job_postings p
// JOIN ops.companies c ON p.company_id = c.id
// WHERE p.week >= (current_week - $weeks)
//   AND (p.position_title ILIKE '%' || $keyword || '%'
//        OR p.skills @> ARRAY[$keyword])
// GROUP BY c.id, c.name, c.segment
// ORDER BY keyword_count DESC
// LIMIT $topN

// 키워드 자동완성 소스: pulse.keyword_index (n8n 스크래핑 시 누적)
```

**키워드 인덱스 테이블 (신규 필요):**
```sql
CREATE TABLE pulse.keyword_index (
  keyword       TEXT PRIMARY KEY,
  category      TEXT,   -- 'skill' | 'role' | 'domain'
  total_count   INT,
  last_seen     DATE
);
-- 검색창 자동완성 + 인기 키워드 제안에 활용
```

---

### Mode C: 복합 키워드

```typescript
interface CompoundKeywordQuery {
  keywords: string[]              // 예: ["Python", "MLOps", "AWS"]
  operator: 'AND' | 'OR'
  weeks: 4 | 8 | 12 | 26 | 52
  topN: 20 | 50 | 100
  segmentId?: string
}

// AND 쿼리 — 모든 키워드를 동시에 채용 중인 기업
// (= 각 키워드별 job_postings가 모두 존재하는 company)
// SELECT c.name, c.segment, COUNT(DISTINCT p.keyword) as matched_keywords,
//        SUM(p.count) as total_postings,
//        array_agg(p.count ORDER BY p.week) as weekly_series
// FROM pulse.job_postings p
// JOIN ops.companies c ON p.company_id = c.id
// WHERE p.week >= (current_week - $weeks)
//   AND p.keyword = ANY($keywords)
// GROUP BY c.id, c.name, c.segment
// HAVING COUNT(DISTINCT p.keyword) = $keywords.length  -- AND 조건
// ORDER BY total_postings DESC LIMIT $topN

// OR 쿼리 — HAVING 절 제거
```

**복합 키워드 UX:**
- 태그 입력 방식: 입력창에 키워드 타이핑 → Enter → 태그로 추가 → `×` 버튼으로 제거
- AND / OR 라디오 토글
- 키워드 최대 5개 제한 (쿼리 복잡도 관리)
- 매칭된 키워드 수 배지 표시 (예: "3/3 키워드 매칭")

---

### 시계열 차트 스펙

```typescript
// 상위 5개 기업은 개별 라인으로 표시
// 6~N위는 "기타 Top {N}" 그룹으로 합산 표시 (회색 점선)
interface TimelineChartConfig {
  topLinesCount: 5           // 개별 라인 수
  groupRestAs: '기타'        // 나머지 그룹 레이블
  xAxis: 'week'              // MM/DD 포맷
  yAxis: 'count'             // 해당 주 공고 수 (Mode A) 또는 키워드 공고 수 (B/C)
  highlight: 'last'          // 마지막 데이터포인트 강조
}
```

---

### 랭킹 테이블 스펙

| 컬럼 | 내용 |
|---|---|
| 순위 | 숫자 (1–N) |
| 기업명 | 클릭 시 View 5 기업 분석으로 이동 |
| 세그먼트 | 색상 배지 |
| 주간 스파크바 | 4–12주 미니 바 차트 (인라인 SVG) |
| 총 공고 수 | Mode A: 전체 합산 / Mode B·C: 키워드 매칭 공고 수 |
| 전주比 변화 | ▲▼ % 표시, 색상 코딩 (녹색/적색) |
| Mode C 한정 | 매칭 키워드 배지 (예: "Python ✓ MLOps ✓ AWS ✓") |

---

### 영업 인텔리전스 활용 시나리오

```
시나리오 1 — 지속 채용 기업 탐지 (영업 타겟)
  Mode A, 12주, Top 50 → 꾸준히 상위 유지 기업 = 서치 의뢰 가능성 높음

시나리오 2 — 특정 스킬 수요 급증 기업 탐지
  Mode B, keyword="Kubernetes", 4주, Top 20 → 인프라 전환 중인 기업 탐지

시나리오 3 — 복합 스킬셋 보유 후보자 배치처 탐색
  Mode C, ["Java", "MSA", "결제"], AND, 8주, Top 30
  → 해당 후보자를 가장 원할 기업 리스트 도출 (이력서 매칭 View와 연계)
```

---

## Harness Feature List 매핑 제안

아래 feature ID를 `feature_list.json`에 추가하거나 기존 항목에 매핑합니다.

| Feature ID | 뷰 | Phase | 의존성 |
|---|---|---|---|
| `dashboard-shell` | 공통 탭 레이아웃 | P2 | — |
| `sd-matrix-chart` | View 1: S/D 매트릭스 | P2 | `pulse.weekly_snapshots` |
| `sd-matrix-drilldown` | View 1: 드릴다운 패널 | P2 | `sd-matrix-chart` |
| `top-companies-list` | View 2: Top 20 랭킹 | P3 | `pulse.job_postings` |
| `top-companies-accordion` | View 2: 포지션 펼침 | P3 | `top-companies-list` |
| `company-timeline-shell` | View 3: 탭·필터 레이아웃 | P3 | `pulse.job_postings` 다주 |
| `company-timeline-mode-a` | View 3: 총 채용 규모 랭킹 | P3 | `company-timeline-shell` |
| `company-timeline-chart` | View 3: 시계열 라인 차트 | P3 | `company-timeline-mode-a` |
| `company-timeline-mode-b` | View 3: 단일 키워드 검색 | P4 | `pulse.keyword_index` |
| `company-timeline-mode-c` | View 3: 복합 키워드 AND/OR | P4 | `company-timeline-mode-b` |
| `keyword-index-table` | pulse.keyword_index 생성/갱신 | P3 | n8n 스크래핑 파이프라인 |
| `hiring-trends-chart` | View 4: 트렌드 라인 | P3 | `pulse.job_postings` 12주 |
| `hiring-trends-drilldown` | View 4: 주차별 드릴다운 | P3 | `hiring-trends-chart` |
| `resume-match-keyword` | View 5: 키워드 매칭 | P4 | — |
| `resume-match-semantic` | View 5: AI 시맨틱 매칭 | P6 | Anthropic API |
| `company-analysis-panel` | View 6: 2패널 기업 분석 | P4 | cross-schema JOIN |
| `company-spark-chart` | View 6: 12주 스파크바 | P4 | `pulse.job_postings` 12주 |

---

## 기술 스택 결정

| 항목 | 선택 | 이유 |
|---|---|---|
| 차트 라이브러리 | **Recharts** 권장 (Chart.js 대안) | React 친화적, TypeScript 타입 완벽, 커스텀 tooltip/드릴다운 용이 |
| 상태 관리 | **Zustand** | 탭별 독립 상태 + 드릴다운 전역 공유 |
| 데이터 페칭 | **TanStack Query** | Supabase 실시간 구독 + 12주 캐싱 |
| 스타일 | **Tailwind CSS** | 기존 VXMI 스택 통일 |

---

*최종 업데이트: 2026-03-17 v2 (CompanyTimeline 추가) | 작성: Claude (Anthropic) | 검토: TimSangmo*
