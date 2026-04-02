# VXMI Hire Intelligence — 통합 PRD v3.0

> **문서 버전:** v3.0 (UX 재설계 + Action Layer 반영)
> **작성일:** 2026-04-02
> **기반 문서:** v2.1 (2026-03-27)
> **변경 범위:** 섹션 3 (Value Layer), 섹션 7 (대시보드 뷰), 섹션 23 (KPI) 전면 개정. 신규: 섹션 7-A (Action Layer), 7-B (후보자 프로파일러), 7-C (시장 신호판), 7-D (OppAlert 피드), 7-E (TDS 시뮬레이터), 섹션 3-A (페르소나별 기본 뷰 구성).

> **v2.1 이하 섹션 중 본 문서에서 다루지 않는 섹션(섹션 1·2·4~6·8~22·24)은 v2.1을 그대로 유지한다. 충돌 시 v3.0이 우선한다.**

---

## 핵심 변경 요약

### 문제 진단 (Why v3.0)

v2.1까지의 대시보드는 **Intelligence(데이터 나열)** 계층에서 멈추고, **Action(행동 권고)** 계층으로 넘어가지 못했다. 결과적으로 유저 반응은 "토스 채용 많네... 그렇네" 수준에 그친다.

**핵심 갭:** 모든 화면이 명사(관찰)로 끝나고, 동사(행동)가 없다.

### 해결 원칙

1. **Action Layer 전면 도입** — 모든 분석 뷰에 "지금 해야 할 것" 패널 부착
2. **페르소나별 진입점 분기** — 온보딩에서 역할을 감지, 메인 뷰를 다르게 구성
3. **신규 Action 뷰 4종 신설** — 후보자 프로파일러 / 시장 신호판 / OppAlert 피드 / TDS 시뮬레이터
4. **Leading KPI 재정의** — B2C 지표를 구독자 수 → 이력서 제출률로 변경

---

## 3. 양면 마켓 구조 및 페르소나 (v3.0 개정)

### 3.2 Value Layer (8단계, v3.0 개정)

> v2.1의 7단계에서 8단계로. **L7: Action Intelligence** 신설.

| Layer | 가치 | 대상 | 플랜 |
|---|---|---|---|
| L0. 커리어 인텔리전스 | 이력서 기반 맞춤 채용 시장 데이터 | 구직자 | Talent Free / Plus |
| L1. 시장 온도계 | S/D 매트릭스, 채용 트렌드 기본 | 모든 채용측 | Starter |
| L2. 시장 신호 | 세그먼트별 신호등 + 지금 해야 할 액션 | 모든 채용측 | Starter (일부) / Pro |
| L3. 후보자 실사 | 후보자 TDS, 상향/하향, 협상 포지션 | 인담·헤드헌터 | Pro |
| L4. 영업 인텔리전스 | OppScore 랭킹, OppAlert, 인재 유출 감지 | 헤드헌터 | Pro |
| L5. 조직 건강 지표 | TDS 시뮬레이터, TDI 시계열, Retention 벤치마크 | CHRO·HR Manager | Enterprise |
| L6. 인재 흐름 추적 | Talent Flow 시계열, 회사 간 인재 이동 | 헤드헌터 + CHRO | Enterprise |
| L7. Action Intelligence | 모든 뷰에 Claude 기반 자연어 해석 + 행동 권고 | 전체 유료 | Pro+ |

### 3.3 페르소나별 핵심 가치 (v3.0 개정)

> v2.1의 Job-to-be-Done을 유지하되, VXMI 가치와 지불 트리거를 Action 중심으로 재정의.

| 페르소나 | Job-to-be-Done | VXMI 핵심 가치 (v3.0) | 지불 트리거 |
|---|---|---|---|
| 인하우스 채용담당자 | 후보자가 좋은 인재인지 + 어떻게 대해야 하는지 빠르게 판단 | **후보자 프로파일러:** TDS + 상향/하향 + 연봉 협상 포지션 + 경쟁 오퍼 예측을 면접 전 5분에 제공 | 프로파일러 5회 소진 → Pro 전환 |
| 헤드헌터 | 콜드콜 전에 이 회사가 왜, 언제부터 막혀 있는지 파악 | **OppAlert 피드:** OTW 급증 + 공고 오픈 동시 감지 → BD 콜 타이밍 알림. 클라이언트 제안서에 S/D 데이터 삽입 | OppAlert 미리보기 3건 소진 |
| HR Manager / CHRO | 채용 퀄리티 정량화 + 경영진 보고 근거 | **TDS 시뮬레이터:** 팀 구성 전/후 인재 밀도 비교. 경쟁사 대비 조직 TDS 포지션 | 시뮬레이터 1회 체험 후 전환 |
| 구직자 | 내 경력의 시장 가치와 이직 최적 타이밍 파악 | **시장 신호판:** 세그먼트별 신호등 + "지금 이직 좋은 시장인가" 즉답. TDS 퍼센타일로 연봉 협상 근거 제공 | 맞춤 알림 3건 소진 / 시장가치 리포트 |

### 3-A. 페르소나별 기본 뷰 구성 (신규)

> 온보딩 페르소나 선택 후, 사이드바 메뉴 순서와 메인 대시보드 진입점이 자동 조정된다.

| 페르소나 | 메인 진입점 (탭 1) | 탭 2 | 탭 3 | 탭 4 (잠금) |
|---|---|---|---|---|
| 인하우스 채용담당자 | 후보자 프로파일러 | 시장 신호판 | Top 기업 볼륨 | TDS 시뮬레이터 (Pro) |
| 헤드헌터 | OppAlert 피드 | 시계열 타임라인 | 후보자 프로파일러 | S/D 매트릭스 |
| HR Manager / CHRO | TDS 시뮬레이터 | 시장 신호판 | S/D 매트릭스 | Retention 벤치마크 (Enterprise) |
| 구직자 | 내 시장가치 | 시장 신호판 | 기업 분석 | 이력서 매칭 |

**구현 방식:**
- `user_profiles.category` 필드로 사이드바 순서를 동적 렌더링
- 기본 대시보드 URL(`/dashboard`)은 카테고리별로 다른 뷰로 redirect
  - 인하우스HR → `/dashboard/candidate-profiler`
  - 헤드헌터 → `/dashboard/opp-alert`
  - CHRO → `/dashboard/tds-simulator`
  - 구직자 → `/dashboard/market-value`

---

## 7. 대시보드 뷰 설계 (v3.0 개정)

### 7.0 Action Layer — 설계 원칙 (신규)

> **모든 분석 뷰에 공통 적용되는 레이어. v3.0의 핵심 설계 원칙.**

#### 7.0.1 "So what?" 패널

모든 분석 뷰의 우측 또는 하단에 **Action Panel**을 상시 노출한다.

```typescript
interface ActionPanel {
  // Claude API가 현재 뷰 데이터를 해석하여 생성
  insight: string;           // 1-2문장: 이 데이터가 의미하는 것
  actions: ActionItem[];     // 1-3개: 지금 해야 할 것
  relatedViews: string[];    // 다음 단계 뷰 링크
}

interface ActionItem {
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  text: string;              // 한국어 행동 권고 (1문장)
  cta?: string;              // 버튼 텍스트 (예: "프로파일러에서 확인")
  ctaUrl?: string;
}
```

#### 7.0.2 Claude API 통합 (Action Intelligence)

```python
# FastAPI 엔드포인트: Action Panel 생성
POST /api/v1/action-panel

# Request Body
{
  "view": "sd-matrix",
  "context": {
    "selectedSegment": "ai-ml",
    "currentData": { "sdRatio": 0.31, "demand": 1620, "supply": 8200 },
    "userCategory": "HEADHUNTER",
    "userPlan": "PRO"
  }
}

# Response
{
  "insight": "AI/ML 엔지니어 세그먼트는 현재 공급이 수요의 31% 수준입니다. 지난 8주 연속 수요가 증가하고 있습니다.",
  "actions": [
    {
      "priority": "HIGH",
      "text": "이 세그먼트에서 수임 중인 포지션은 클라이언트에게 S/D 데이터를 제시하며 fee 상향 협상 가능합니다.",
      "cta": "클라이언트 제안서 생성",
      "ctaUrl": "/dashboard/opp-alert?segment=ai-ml"
    }
  ],
  "relatedViews": ["opp-alert", "candidate-profiler"]
}
```

**Claude 모델:** `claude-sonnet-4-20250514` (Pro+에서만 활성화)
**캐시 TTL:** 동일 context hash 기준 1시간
**Fallback:** API 실패 시 rule-based 정적 텍스트로 대체

#### 7.0.3 Action Panel 플랜별 접근

| 플랜 | Action Panel |
|---|---|
| Starter / Talent Free | 잠금 오버레이 + "Pro에서 AI 해석 보기" CTA |
| Pro | Claude 기반 insight + actions 전체 표시 |
| Enterprise | Pro + 경영진 리포트 자동 생성 버튼 추가 |

---

### 7.1~7.7 기존 뷰 (v2.1 유지 + Action Panel 추가)

> v2.1의 View 1~6 (SDMatrix, TopCompanies, CompanyTimeline, HiringTrends, ResumeMatch, CompanyAnalysis)는 뷰 로직을 유지하되, 모든 뷰에 **7.0에서 정의한 Action Panel을 우측 패널로 추가**한다.

**레이아웃 변경:**

```
// 기존 (v2.1)
<MainContent>  // 100% width

// v3.0
<MainContent>  // 66% width
<ActionPanel>  // 34% width, sticky
```

모바일(< 768px)에서는 Action Panel이 MainContent 하단으로 이동.

---

### 7-B. 후보자 프로파일러 (신규, Phase 2)

**라우트:** `/dashboard/candidate-profiler`
**플랜:** Starter 5회/월 (맛보기) → Pro 200명/월 → Enterprise 2,000명/월

#### 입력 스키마

```typescript
interface CandidateProfilerInput {
  // 방식 1: 레쥬메 스니펫 (자유 텍스트)
  resumeText?: string;         // 최대 3,000자
  
  // 방식 2: 구조화 입력
  currentCompany?: string;     // 현 재직사명
  yearsOfExperience?: number;
  education?: string;          // 최종 학력 (학교+전공)
  skills?: string[];
  
  // 컨텍스트
  targetCompanyId?: string;    // 지원 회사 (당사) - TDS 비교용
}
```

#### 출력 스키마

```typescript
interface CandidateProfilerOutput {
  tdsScore: number;              // 0~100. 산출식: EDS×0.45 + CDS×0.35 + PDS×0.20
  tdsPercentile: number;         // 세그먼트 내 상위 N%
  
  applicationDirection: {
    type: 'UPWARD' | 'LATERAL' | 'DOWNWARD';
    candidateTds: number;        // 후보자 TDS
    targetCompanyTds: number;    // 지원 회사 TDS
    deltaPercent: number;        // 차이 %
  };
  
  salaryNegotiation: {
    marketP25: number;           // 만원 단위
    marketP50: number;
    marketP75: number;
    recommendedLeverage: 'HIGH' | 'MEDIUM' | 'LOW';
    // HIGH: 시장 P75 이상 요구 가능
    // MEDIUM: P50~P75
    // LOW: P50 이하, 비금전 요소 중심 설득 권장
  };
  
  motivationEstimate: {
    primary: '연봉' | '도메인전환' | '워라밸' | '조직문화' | '커리어성장';
    confidence: number;          // 0~1
    basis: string;               // 추정 근거 1문장
  };
  
  competingOffers: {
    companyId: string;
    companyName: string;
    tdsScore: number;
    likelihood: 'HIGH' | 'MEDIUM' | 'LOW';
  }[];                           // TDS 유사 구간 기업 Top 5
  
  actionPanel: ActionPanel;      // 7.0.1 기준
}
```

#### 핵심 산출 로직

```python
# TDS 계산 (기존 정의 유지)
# EDS: 학력 점수 (QS 2025 기준 티어 매핑)
# CDS: 경력 점수 (재직사 TDS × 재직 기간 가중)
# PDS: 전문성 점수 (세그먼트 내 스킬 희소성)

def calculate_tds(resume_parsed: dict) -> float:
    eds = calculate_eds(resume_parsed['education'])
    cds = calculate_cds(resume_parsed['career'])
    pds = calculate_pds(resume_parsed['skills'], resume_parsed['segment'])
    return eds * 0.45 + cds * 0.35 + pds * 0.20

# 상향/하향 판단
def classify_application_direction(candidate_tds: float, target_tds: float) -> str:
    delta = (candidate_tds - target_tds) / target_tds
    if delta > 0.10:    return 'DOWNWARD'   # 후보자가 10%+ 높음
    elif delta < -0.10: return 'UPWARD'
    else:               return 'LATERAL'

# 경쟁 오퍼 예측: ops.companies에서 candidate_tds ± 8p 구간 기업 추출
def get_competing_offers(candidate_tds: float, segment_id: str) -> list:
    return db.query(Company).filter(
        Company.segment_id == segment_id,
        Company.avg_tds.between(candidate_tds - 8, candidate_tds + 8)
    ).order_by(Company.avg_tds.desc()).limit(5).all()
```

#### UX 인터랙션

1. **입력 방식 토글:** "레쥬메 붙여넣기" / "직접 입력" 탭 전환
2. **분석 소요 시간:** 스트리밍 결과 표시 (TDS → 방향성 → 협상 → 경쟁사 순서로 순차 표시)
3. **Bulk 입력 (Pro+):** CSV 업로드 → 최대 200명 일괄 분석 → 테이블 + CSV 다운로드
4. **저장 기능:** 분석 결과를 후보자 카드로 저장 (localStorage → Pro에서 서버 동기화)

---

### 7-C. 시장 신호판 (신규, Phase 1b)

**라우트:** `/dashboard/market-signals`
**플랜:** Starter (14세그먼트 현재 주차) → Pro (12주 추세 + 드릴다운) → Enterprise (52주 + 예측)

#### 데이터 스키마

```typescript
interface MarketSignal {
  segmentId: string;
  segmentName: string;
  
  currentRatio: number;          // 현재 S/D Ratio
  signal: 'RED' | 'YELLOW' | 'GREEN';
  // RED:    ratio < 0.5  (공급 희소 — 채용 어려움 / 구직자 협상력 높음)
  // YELLOW: 0.5 ≤ ratio < 1.0 (균형)
  // GREEN:  ratio ≥ 1.0  (공급 우위 — 채용 용이 / 구직자 경쟁 치열)
  
  trend4w: number;               // 4주 전 대비 변화율 (%)
  trend12w: number;              // 12주 전 대비 변화율 (%)  [Pro+]
  
  actionTextByCategory: {        // 페르소나별 다른 행동 권고
    [category: string]: string;
  };
  
  weeklyHistory: {               // 12주 미니 스파크라인 [Pro+]
    week: string;
    ratio: number;
  }[];
}
```

#### 신호 기준 및 Action Text 생성 규칙

```python
SIGNAL_THRESHOLDS = {
    'RED':    lambda r: r < 0.5,
    'YELLOW': lambda r: 0.5 <= r < 1.0,
    'GREEN':  lambda r: r >= 1.0,
}

ACTION_TEMPLATES = {
    'RED': {
        'INHOUSE_HR':   '공급 부족 시장입니다. 파이프라인을 즉시 열고 후보자 응답률을 높이는 JD 리라이팅을 권장합니다.',
        'HEADHUNTER':   'fee 협상 시 이 S/D 데이터를 클라이언트에게 제시하면 수임료 상향이 가능합니다.',
        'CHRO':         '헤드헌터 수임을 검토하세요. 직접 채용보다 성공 확률이 높습니다.',
        'JOB_SEEKER':   '지금이 이직 협상력 최대 구간입니다. 복수 오퍼를 병행하세요.',
    },
    'YELLOW': {
        'INHOUSE_HR':   '표준 채용 전략이 유효합니다. 4주 추세를 주시하세요.',
        'HEADHUNTER':   '표준 서치 구간입니다. 후보자 품질(TDS)에 집중하세요.',
        'CHRO':         '균형 시장입니다. 현재 채용 채널을 유지하세요.',
        'JOB_SEEKER':   '보통 시장입니다. 차별화된 레쥬메와 포트폴리오가 핵심입니다.',
    },
    'GREEN': {
        'INHOUSE_HR':   '공급 우위입니다. 직접 채용 채널을 활용하고 헤드헌터 수임 예산을 절감하세요.',
        'HEADHUNTER':   '이 세그먼트 수임은 낮은 우선순위입니다. RED 세그먼트에 집중하세요.',
        'CHRO':         '직접 채용 채널이 효율적입니다.',
        'JOB_SEEKER':   '경쟁이 치열한 시장입니다. 6개월 후 재검토하거나 인접 세그먼트로 전환을 고려하세요.',
    },
}
```

#### 화면 구조

```
[신호판 그리드]  — 14개 세그먼트 카드 (신호등 색상 + ratio + 4주 추세)
       ↓ 클릭
[세그먼트 상세 패널] — 12주 스파크라인 + 상세 수치 + Action Text (페르소나별)
       ↓
[Action Panel]  — Claude 기반 해석 (Pro+)
```

---

### 7-D. OppAlert 피드 (신규, Phase 2 — 헤드헌터 전용)

**라우트:** `/dashboard/opp-alert`
**플랜:** Pro (주 10건 알림) → Enterprise (무제한 + Slack/이메일 자동 발송)
**대상 페르소나:** 헤드헌터 (다른 페르소나는 접근 시 페르소나 변경 안내)

#### OppAlert 트리거 조건

```python
# 기업별 OppAlert 생성 조건 (AND 로직)
OPP_ALERT_CONDITIONS = {
    'PRIMARY': {
        # 이 기업의 OTW 비율이 최근 4주간 20%+ 증가
        'otw_increase': lambda prev, curr: (curr - prev) / prev >= 0.20,
    },
    'SECONDARY': {
        # 동 기간 외부 채용 공고 신규 오픈 (1건 이상)
        'new_postings': lambda count: count >= 1,
    },
    'BOOSTERS': [
        # 아래 중 1개 이상 해당 시 우선순위 CRITICAL로 상향
        lambda data: data['sd_ratio'] < 0.5,         # 공급 희소 세그먼트
        lambda data: data['posting_weeks'] >= 8,     # 8주 이상 채용 지속
        lambda data: data['week_over_week'] >= 0.30, # 이번 주 급증
    ]
}

# OppScore 산출 (0~100)
def calculate_opp_score(company: Company, segment: Segment) -> float:
    otw_score    = min(company.otw_increase_4w * 100, 30)  # max 30pt
    hiring_score = min(company.active_postings * 2, 25)    # max 25pt
    sd_score     = max(0, (1 - segment.sd_ratio) * 25)     # max 25pt
    tenure_score = min(company.hiring_weeks * 2.5, 20)     # max 20pt
    return otw_score + hiring_score + sd_score + tenure_score
```

#### 알림 카드 스키마

```typescript
interface OppAlert {
  id: string;
  companyId: string;
  companyName: string;
  segment: string;
  oppScore: number;             // 0~100
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  
  triggers: {
    otwIncrease: number;        // 4주 OTW 증가율 (%)
    newPostings: number;        // 신규 공고 수
    hiringWeeks: number;        // 연속 채용 기간 (주)
    sdRatio: number;            // 현재 세그먼트 S/D Ratio
  };
  
  bdScript: string;             // 자동 생성된 BD 콜 스크립트 (1문단)
  proposalDataPoints: string[]; // 클라이언트 제안서용 데이터 포인트
  
  createdAt: DateTime;
  expiresAt: DateTime;          // 2주 후 만료
}
```

#### BD 스크립트 자동 생성

```python
# Claude API를 통한 BD 콜 스크립트 생성
BD_SCRIPT_PROMPT = """
다음 데이터를 기반으로 헤드헌터가 {company_name}에 처음 전화할 때 사용할 
BD 스크립트를 3-4문장으로 작성해주세요. 데이터를 자연스럽게 언급하되, 
강압적이지 않고 인텔리전스를 제공하는 느낌으로 작성해주세요.

- OTW 증가: {otw_increase}% (4주 기준)
- 현재 채용 공고: {active_postings}개
- 세그먼트 S/D Ratio: {sd_ratio} ({signal})
- 채용 지속 기간: {hiring_weeks}주

출력: 한국어 3-4문장 스크립트만. 인사말 없이.
"""
```

---

### 7-E. TDS 시뮬레이터 (신규, Phase 3 — HR Manager/CHRO 전용)

**라우트:** `/dashboard/tds-simulator`
**플랜:** Enterprise (Starter/Pro는 1회 체험 후 잠금)
**대상 페르소나:** HR Manager, CHRO (다른 페르소나도 접근 가능하나 팀 데이터 입력 기능 잠금)

#### 기능 명세

**1. 팀 TDS 산출**

```typescript
interface TeamMember {
  name?: string;               // 선택 (익명화 가능)
  education: string;           // 학교 + 학위
  careerHistory: {
    company: string;
    years: number;
  }[];
  skills: string[];
}

interface TeamTDSResult {
  teamAvgTds: number;
  teamTdsDistribution: {       // 팀원 TDS 분포
    p25: number;
    p50: number;
    p75: number;
  };
  industryBenchmark: {
    sameSegmentAvg: number;
    top10PercentThreshold: number;
  };
  weaknessAnalysis: string;    // "EDS 취약: 상위 학력 비중 낮음" 등
}
```

**2. 채용 시뮬레이션**

```typescript
interface HiringSimulation {
  currentTeamTds: number;
  
  scenarios: {
    candidate: TeamMember;
    projectedTeamTds: number;   // 이 후보자 합류 시
    tdsDelta: number;           // 변화량
    recommendation: 'STRONG_YES' | 'YES' | 'NEUTRAL' | 'NO';
    rationale: string;          // 1-2문장 추천 근거
  }[];
}
```

**3. 경쟁사 TDS 비교 (Enterprise)**

```typescript
interface CompetitorTDSBenchmark {
  targetCompanyId: string;
  targetCompanyTds: number;
  competitors: {
    companyId: string;
    companyName: string;
    tds: number;
    delta: number;              // 우리 회사 대비
  }[];
  recommendation: string;       // "경쟁사 대비 +8p 상승을 위한 채용 전략"
}
```

#### UX 플로우

```
Step 1: 팀 구성원 입력 (CSV 업로드 or 직접 입력)
  ↓
Step 2: 팀 TDS 리포트 표시 (분포 차트 + 업계 벤치마크)
  ↓
Step 3: 후보자 추가 시뮬레이션 (1~5명 비교)
  ↓
Step 4: 채용 결정 권고 + 경영진 리포트 PDF 다운로드 (Enterprise)
```

---

## 23. 성공 지표 (KPIs) — v3.0 개정

### 23.1 서비스 운영 KPI (v2.1 유지)

*변경 없음.*

### 23.2 비즈니스 KPI (v3.0 개정)

> **핵심 변경:** B2C Leading KPI를 "구독자 수"에서 "이력서 제출률"로 변경.
> 
> **근거:** 플라이휠 구조상 이력서 풀이 커야 채용측 가치가 상승한다. 구독자 수는 Lagging KPI. 이력서 제출률이 진짜 엔진이다.

#### 신규 North Star 메트릭 체계

| 트랙 | North Star | 이유 |
|---|---|---|
| **B2C (구직자)** | 이력서 제출률 (누적 이력서 수) | 헤드헌팅 매칭 품질의 직접적 선행 지표 |
| **B2B (채용측)** | Pro 구독자 수 | 반복 MRR의 핵심 |
| **전체 플랫폼** | 매칭 성사 건수 (헤드헌팅 클로즈) | 플라이휠 회전의 결과 지표 |

#### 주요 KPI 목표 (v3.0 개정)

| KPI | 측정 기준 | 6개월 목표 | 12개월 목표 |
|---|---|---|---|
| **B2C Leading KPI** | | | |
| 누적 이력서 제출 수 | Talent 계정 × 이력서 업로드 완료 | 3,000건 | 15,000건 |
| 이력서 제출 완료율 | 가입자 중 이력서 업로드한 비율 | 70%+ | 80%+ |
| Opt-in 매칭 풀 동의율 | Talent 유저 중 헤드헌팅 매칭 동의 | 30%+ | 40%+ |
| **B2C Lagging KPI** | | | |
| Talent Free 가입 | - | 4,000 | 20,000 |
| Talent Plus 전환율 | Free → Plus | 5% | 8% |
| **B2B 핵심 KPI** | | | |
| Pro 구독자 수 | - | 50명 | 280명 |
| 후보자 프로파일러 → Pro 전환 | Starter에서 5회 소진 후 전환 | 15% | 22% |
| OppAlert → Pro 전환 | 헤드헌터 미리보기 3건 소진 후 | 20% | 30% |
| Enterprise 전환율 | Pro → Enterprise | 5% | 10% |
| **헤드헌팅 수익** | | | |
| 매칭 성사 건수 | 플랫폼 경유 헤드헌팅 클로즈 | 5건/월 | 30건/월 |
| 평균 플레이스먼트 fee | 클로즈 건당 평균 수수료 | 3,000만원 | 3,500만원 |
| **전체 MRR** | | | |
| Subscription MRR | 구독 수익 | 5,500,000원 | 42,000,000원 |
| Performance Revenue | 헤드헌팅 fee 수익 | 15,000,000원 | 105,000,000원 |

### 23.3 Action Layer KPI (신규)

> Action Panel 도입의 실질적 효과를 측정.

| KPI | 목표 |
|---|---|
| Action Panel CTR | 노출 대비 CTA 클릭률 > 15% |
| Action-to-View 전환 | Action Panel에서 관련 뷰 이동률 > 25% |
| Pro 전환 중 Action Panel 경유 비율 | 신규 Pro 전환의 > 40%가 Action Panel CTA 경유 |
| 후보자 프로파일러 재방문율 | 7일 내 재방문 > 60% |

---

## 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|---|---|---|---|
| v1.0 | 2026-03-20 | Claude (Anthropic) | 초안 |
| v2.0 | 2026-03-20 | Claude (Anthropic) | Architect/Critic 피드백 반영 통합본 |
| v2.1 | 2026-03-27 | Claude (Anthropic) | UI 목업 HTML 추가 |
| **v3.0** | **2026-04-02** | **Claude (Anthropic)** | **UX 재설계 반영. Action Layer 전면 도입. 신규 뷰 4종 (후보자 프로파일러, 시장 신호판, OppAlert 피드, TDS 시뮬레이터). 페르소나별 진입점 분기. B2C North Star = 이력서 제출률로 변경. Value Layer 8단계로 확장.** |

---

*본 문서는 밸류커넥트 내부 문서입니다.*
*v3.0 - 2026-04-02 | 작성: Claude (Anthropic) | 검토: TimSangmo*