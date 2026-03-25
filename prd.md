# VXMI Hire Intelligence - 통합 PRD (Product Requirements Document)

> **문서 버전:** v2.0 (통합본)
> **작성일:** 2026-03-20
> **최종 수정:** 2026-03-20
> **작성:** 밸류커넥트 프로덕트팀
> **상태:** Final Draft
> **도메인:** valuehire.cc
> **프로젝트:** Hire-Intelligence / vxmi-dashboard

---

## 목차

1. [개요](#1-개요)
2. [용어 정의 및 통일 기준](#2-용어-정의-및-통일-기준)
3. [양면 마켓 구조 및 페르소나](#3-양면-마켓-구조-및-페르소나)
4. [플랜 구조 (2-Track, 5-Tier)](#4-플랜-구조-2-track-5-tier)
5. [사용자 역할 및 권한 체계 (RBAC)](#5-사용자-역할-및-권한-체계-rbac)
6. [멀티 테넌시 설계](#6-멀티-테넌시-설계)
7. [대시보드 뷰 설계](#7-대시보드-뷰-설계)
8. [관리자 패널 (SuperAdmin)](#8-관리자-패널-superadmin)
9. [User 셀프서비스 대시보드](#9-user-셀프서비스-대시보드)
10. [기술 아키텍처](#10-기술-아키텍처)
11. [데이터 모델](#11-데이터-모델)
12. [API 설계](#12-api-설계)
13. [데이터 파이프라인](#13-데이터-파이프라인)
14. [확장성 및 성능 전략](#14-확장성-및-성능-전략)
15. [인증 및 보안](#15-인증-및-보안)
16. [개인정보보호법(PIPA) 준수](#16-개인정보보호법pipa-준수)
17. [리스크 관리](#17-리스크-관리)
18. [테스트 전략](#18-테스트-전략)
19. [모니터링 및 옵저버빌리티](#19-모니터링-및-옵저버빌리티)
20. [GA4 이벤트 설계](#20-ga4-이벤트-설계)
21. [로드맵](#21-로드맵)
22. [팀 구성](#22-팀-구성)
23. [성공 지표 (KPIs)](#23-성공-지표-kpis)
24. [부록](#24-부록)

---

## 1. 개요

### 1.1 프로젝트 배경

밸류커넥트(ValueConnect)는 한국 채용 시장의 수요-공급 인텔리전스를 제공하는 플랫폼 **Hire Intelligence**(valuehire.cc)를 구축한다. VXMI(ValueConnect Market Intelligence)는 이 플랫폼의 데이터 분석 엔진 브랜드명이다.

### 1.2 현재 상태

| 항목 | 상태 |
|---|---|
| 프론트엔드 (vxmi-dashboard) | React 19 + TypeScript + Vite 8 + Tailwind CSS 4 + Recharts [MVP-완료] |
| 6개 분석 뷰 | Mock 데이터 기반 구현 완료 [MVP-완료] |
| 라우팅 | useState 기반 탭 네비게이션 (React Router 미적용) |
| 상태관리 | 로컬 useState만 사용 (라이브러리 없음) |
| 인증 | Mock 로그인 모달만 존재 (실제 인증 없음) |
| 백엔드 | 없음. 모든 데이터 하드코딩 (`src/data/*.ts`) |
| 데이터 수집 | n8n 기반 스크래핑 파이프라인 설계 단계 |

### 1.3 프로젝트 목표

1. 양면 마켓 플랫폼 구축 (구직자 Track + 채용측 Track)
2. 실시간 채용 시장 인텔리전스 대시보드 운영
3. RBAC 기반 관리자/사용자 시스템 구축
4. 멀티 테넌시 지원 (조직 단위 접근 관리)
5. 데이터 파이프라인 자동화 및 안정화

### 1.4 이 문서의 범위

본 PRD는 다음 문서들을 **통합하여 대체하는 마스터 문서**이다:

| 기존 문서 | 본 PRD에서 다루는 섹션 |
|---|---|
| `dashboard-design.md` | 섹션 7 (대시보드 뷰 설계) |
| `VXMI-Pricing-Plan.md` v3 | 섹션 3, 4 (마켓 구조, 플랜) |
| `PRD-Admin-Panel.md` v1 | 섹션 5, 8, 9, 12 (RBAC, 관리자, API) |

기존 문서들은 참고 자료로 보존하되, **요구사항 충돌 시 본 PRD가 우선**한다.

---

## 2. 용어 정의 및 통일 기준

> **중요:** 기존 문서 간 용어 불일치가 존재했다. 본 PRD에서는 Pricing v3 기준으로 통일한다.

### 2.1 요금제 (Pricing Tiers) -- 통일 기준

| Track | Tier | 가격 | 비고 |
|---|---|---|---|
| **구직자 (Talent)** | Talent Free | 0원 | 이력서+LinkedIn 인증 필수 |
| **구직자 (Talent)** | Talent Plus | 9,900원/월 | |
| **채용측 (Business)** | Starter | 0원 | 무료 |
| **채용측 (Business)** | Pro | 49,000원/월 | |
| **채용측 (Business)** | Enterprise | 149,000원/월~ | |

**폐기된 용어:** "Free/Basic/Pro/Enterprise" 4-tier 구조 (PRD-Admin-Panel에서 사용)는 본 PRD의 2-Track 5-Tier로 대체한다. Admin Panel의 `Basic` tier는 제거하고, 구직자 Track의 `Talent Plus`가 해당 가격대를 흡수한다.

### 2.2 사용자 역할 (RBAC Roles) -- 통일 기준

| 역할 | 설명 | 비고 |
|---|---|---|
| **SuperAdmin** | 밸류커넥트 내부 운영팀 | 전체 시스템 관리 |
| **User** | 서비스 가입 사용자 | 카테고리별 세분화 |
| **Guest** | 미로그인 방문자 | 제한적 열람 |

**사용자 카테고리** (User 하위 분류):

| 카테고리 | Track | 허용 요금제 |
|---|---|---|
| 구직자 | Talent | Talent Free, Talent Plus |
| 인하우스HR | Business | Starter, Pro, Enterprise |
| 헤드헌터 | Business | Starter, Pro, Enterprise |
| CHRO/인사담당자 | Business | Starter, Pro, Enterprise |

**폐기된 용어:** "Viewer/Analyst/Admin" 역할 구분은 사용하지 않는다. "Admin"은 SuperAdmin으로만 사용한다.

### 2.3 핵심 용어

| 용어 | 정의 |
|---|---|
| S/D Ratio | Supply/Demand Ratio. 인재 공급 대비 채용 수요 비율 |
| OTW (Open To Work) | LinkedIn에서 이직 의향을 표시한 인재 비율 |
| OppScore | Opportunity Score. 영업 기회 점수 |
| TDI | Talent Density Index. 인재밀도 지수 |
| RPS | Recruiter Pool Size. LinkedIn Recruiter 인재 풀 사이즈 |
| Organization | 멀티 테넌시의 기본 단위. 회사/팀/서치펌 등 |

---

## 3. 양면 마켓 구조 및 페르소나

### 3.1 플라이휠 구조

```
구직자가 이력서 제출 + LinkedIn 인증
       |
       v
이력서 데이터 풀 확대 -> 인재밀도 산출 정확도 상승
       |
       v
채용측 (리크루터/헤드헌터/CHRO) 가치 상승 -> 유료 전환 상승
       |
       v
매칭 품질 상승 -> 구직자에게 더 정확한 채용 알림 제공
       |
       v
구직자 유입 상승 -> 선순환
```

### 3.2 Value Layer (7단계)

| Layer | 가치 | 대상 | 플랜 |
|---|---|---|---|
| L0. 커리어 인텔리전스 | 이력서 기반 맞춤 채용 시장 데이터 | 구직자 | Talent Free / Plus |
| L1. 시장 온도계 | S/D 매트릭스, 채용 트렌드 기본 | 모든 채용측 | Starter |
| L2. 후보자 스코어링 | 후보자 bulk 입력, 출신 회사 인재밀도 점수화 | 인하우스 리크루터 | Pro |
| L3. 영업 인텔리전스 | OppScore 랭킹, 인재 유출 감지 | 헤드헌터 | Pro |
| L4. 조직 건강 지표 | TDI 시계열, Retention 벤치마크 | CHRO | Enterprise |
| L5. 인재 흐름 추적 | Talent Flow 시계열, 회사 간 인재 이동 | 헤드헌터 + CHRO | Enterprise |
| L6. 예측 & AI | 수요 예측, AI 시맨틱 매칭, 이탈 리스크 | 전체 파워 유저 | Enterprise |

### 3.3 페르소나별 핵심 가치

| 페르소나 | 사이드 | Job-to-be-Done | VXMI 가치 | 지불 트리거 |
|---|---|---|---|---|
| 구직자 | Supply | 내 경력에 맞는 채용 기회를 놓치지 않고 싶다 | 이력서 기반 맞춤 채용 구독 + 시장 내 포지션 가치 확인 | 맞춤 알림 횟수 / 시장가치 리포트 |
| 인하우스 리크루터 | Demand | 후보자가 좋은 인재인지 빠르게 판단 | 후보자 bulk 스코어링, 출신 회사 인재밀도 | 스코어링 횟수 소진 |
| 헤드헌터 | Demand | 어떤 회사에 콜드콜해야 성사율 높은지 | OppScore 랭킹 + 인재 유출 감지 | 영업 시그널 접근 제한 |
| CHRO/인사담당자 | Demand | 채용 퀄리티가 올라가고 있는지 경영진에 보고 | TDI 시계열 + Retention 벤치마크 | 시계열/벤치마크 데이터 |

---

## 4. 플랜 구조 (2-Track, 5-Tier)

### 4.1 Track A: 구직자 (Talent)

#### 가입 Gate

```
Step 1: 이력서 업로드 (PDF/DOCX 또는 직접 입력)
Step 2: LinkedIn 프로필 인증 (OAuth) -> 경력 자동 연동 + 본인 확인
Step 3: 관심 세그먼트 선택 (최대 3개)
Step 4: Talent Free 활성화
```

#### Talent Free (0원)

| 카테고리 | 기능 | 제한 |
|---|---|---|
| 시장 현황 | 내 세그먼트 S/D 매트릭스 | 선택한 세그먼트만 (최대 3개) |
| 채용 트렌드 | 내 세그먼트 4주 트렌드 | 4주만 |
| Top 채용 기업 | 내 세그먼트 Top 10 | 기업명만 (상세 불가) |
| 내 시장가치 | Market Position 카드 | 월 1회 갱신 |
| 맞춤 채용 알림 | 이력서 기반 공고 알림 | 주 1회 이메일 (Top 3건) |

#### Talent Plus (9,900원/월)

Talent Free 전체 + 실시간 맞춤 알림(일간 무제한), 상세 기업 정보(월 20개), 경쟁력 분석(월 5회), 시장가치 시계열(주간), 세그먼트 무제한, 12주 히스토리, 키워드 알림(5개), AI 이력서 개선 제안(월 3회)

### 4.2 Track B: 채용측 (Business)

#### Starter (0원)

| 카테고리 | 기능 | 제한 |
|---|---|---|
| S/D 매트릭스 | 14개 세그먼트 | 주 1회 스냅샷 |
| Top 기업 랭킹 | Top 20 | 최신 주차만, 히스토리 없음 |
| 채용 트렌드 | 세그먼트별 4주 | 5개 기본 세그먼트만 |
| 기업 분석 | 기업 프로필 카드 | 월 3개 기업 |
| 후보자 스코어링 | 1명씩 | 월 5회 (맛보기) |
| 데이터 갱신 | 주 1회 (월요일) | - |

#### Pro (49,000원/월)

Starter 전체 + Bulk 후보자 스코어링(월 200명), 파이프라인 품질 대시보드, OppScore 랭킹, 인재 유출 시그널(주 10건), S/D 드릴다운, Top 50 기업, CompanyTimeline Mode A+B, 14개 세그먼트 12주, 기업 분석 무제한, 이력서 키워드 매칭(월 30회), 주 2회 갱신, 주간 이메일, CSV 내보내기

#### Enterprise (149,000원/월~)

Pro 전체 + TDI 시계열(52주), Retention 벤치마크, 채용 브랜드 건강도, 경영진 리포트 자동 생성, 인재 유출 상세/경쟁사 맵, 영업 브리핑 자동 생성, Bulk 스코어링(월 2,000명), AI 시맨틱 매칭(월 200회), 역매칭, Talent Flow 전체, CompanyTimeline Mode C, 채용 수요 예측, 일간 갱신, 실시간 Slack/Telegram, CSV+PDF+REST API(월 10,000콜), 전담 CSM

### 4.3 전환 퍼널

```
[구직자 Track]
Talent Free -> (맞춤 알림 3건 제한, 시장가치 트리거) -> Talent Plus

[채용측 Track]
Starter -> (스코어링 5회 소진, OppScore 접근) -> Pro (14일 무료 체험)
Pro -> (TDI 시계열, Talent Flow, AI 매칭) -> Enterprise (데모 미팅)

[Cross-Track]
Talent Plus opt-in -> Enterprise AI 매칭 풀 -> 양측 가치 증가
```

### 4.4 구직자 데이터 활용 정책

1. **익명 집계 데이터** (모든 Talent 유저): 인재밀도 산출, S/D Ratio, 세그먼트별 공급 통계. 개인 식별 불가.
2. **매칭 후보자 풀** (Talent Plus opt-in만): Enterprise AI 매칭 대상. 매칭 시 양측 알림.
3. **절대 금지**: 이력서 원문 직접 전달, opt-in 없는 개인정보 노출, 동의 없는 연락처 공유.

---

## 5. 사용자 역할 및 권한 체계 (RBAC)

### 5.1 역할 정의

#### SuperAdmin (밸류커넥트 내부)

| 항목 | 설명 |
|---|---|
| 대상 | 밸류커넥트 운영팀, C-Level, 개발팀 |
| 생성 방식 | 내부 초대 전용 (자체 회원가입 불가) |
| 핵심 권한 | 전체 시스템 관리, 유저/과금/데이터 무제한 |
| 세션 만료 | 8시간 |

#### User (일반 사용자)

| 항목 | 설명 |
|---|---|
| 대상 | 서비스 가입 사용자 |
| 생성 방식 | Google OAuth (MVP) |
| 카테고리 | 구직자, 인하우스HR, 헤드헌터, CHRO/인사담당자 |
| 핵심 권한 | 자신의 계정 관리, 요금제에 따른 데이터 접근 |
| 세션 만료 | 24시간 (Remember Me: 30일) |

#### Guest (미인증 방문자)

| 항목 | 설명 |
|---|---|
| 대상 | 미로그인 방문자 |
| 핵심 권한 | 제한된 샘플 데이터 (상위 5건), 회원가입 유도 |

### 5.2 API-Level 권한 매트릭스

| 리소스:액션 | SuperAdmin | User (Starter) | User (Pro) | User (Enterprise) | Guest |
|---|:---:|:---:|:---:|:---:|:---:|
| **분석 뷰** | | | | | |
| S/D 매트릭스 - 조회 | 전체 | 14세그먼트 | 전체+드릴다운 | 전체+드릴다운 | 상위 5건 |
| Top 기업 - 조회 | 전체 | Top 20 | Top 50 | Top 100 | 상위 5건 |
| CompanyTimeline | 전체 | - | Mode A+B | Mode A+B+C | - |
| 채용 트렌드 | 전체 | 4주/5세그 | 12주/14세그 | 52주/14+커스텀 | - |
| 이력서 매칭 | 전체 | - | 키워드(월30) | AI시맨틱(월200) | - |
| 기업 분석 | 전체 | 월 3개 | 무제한 | 무제한 | - |
| **후보자 스코어링** | 무제한 | 월 5회(1명씩) | 월 200명(bulk) | 월 2,000명(bulk) | - |
| **데이터 관리** | | | | | |
| 무제한 Pagination | O | - | - | - | - |
| CSV Export | O | - | O | O | - |
| PDF Export | O | - | - | O | - |
| REST API | O | - | - | 월 10,000콜 | - |
| Raw 데이터 조회 | O | - | - | - | - |
| **관리 기능** | | | | | |
| 유저 관리 | O | - | - | - | - |
| 과금/빌링 관리 | O | - | - | - | - |
| 트래픽 모니터링 | O | - | - | - | - |
| 시스템 설정 | O | - | - | - | - |

### 5.3 권한 검증 흐름

```
Client -> Router -> AuthGuard -> TokenService (JWT 검증)
  -> 유효: RoleGuard (역할+요금제 확인) -> 접근 허용 / 403 Forbidden
  -> 만료: Refresh Token 시도 -> 성공: 새 Access Token / 실패: 로그인 리다이렉트
```

---

## 6. 멀티 테넌시 설계

### 6.1 Organization 엔터티

멀티 테넌시를 지원하기 위해 `Organization` 엔터티를 도입한다. 모든 비즈니스 데이터 테이블에 `organization_id`를 포함한다.

```typescript
interface Organization {
  id: string;                    // UUID
  name: string;                  // 조직명 (예: "밸류커넥트", "ABC서치")
  type: 'SEARCH_FIRM' | 'CORPORATION' | 'INDIVIDUAL';
  plan: 'STARTER' | 'PRO' | 'ENTERPRISE';
  billingEmail: string;
  maxSeats: number;              // 최대 시트 수
  activeSeats: number;           // 현재 활성 시트
  settings: OrganizationSettings;
  createdAt: DateTime;
  updatedAt: DateTime;
}

interface OrganizationSettings {
  allowedSegments: string[];     // 접근 허용 세그먼트 (Enterprise 커스텀)
  dataRetentionWeeks: number;    // 데이터 보존 기간
  ssoEnabled: boolean;           // SSO 활성화 (Enterprise)
  customBranding: boolean;       // 화이트라벨 (Enterprise 애드온)
}
```

### 6.2 조직-사용자 관계

```typescript
interface OrganizationMember {
  id: string;
  organizationId: string;        // FK -> organizations.id
  userId: string;                // FK -> users.id
  orgRole: 'OWNER' | 'ADMIN' | 'MEMBER';
  joinedAt: DateTime;
}
```

### 6.3 데이터 격리 원칙

- **Row-Level Security (RLS)**: Supabase RLS 정책으로 `organization_id` 기반 데이터 격리
- **API 레벨**: 모든 쿼리에 `organization_id` 필터 자동 주입 (미들웨어)
- **Cross-org 접근**: SuperAdmin만 가능. 일반 유저는 자신의 Organization 데이터만 접근

### 6.4 팀 시트 기반 할인

| 시트 수 | Pro (인당/월) | Enterprise (인당/월) |
|---|---|---|
| 1명 | 49,000원 | 149,000원 |
| 2~5명 | 42,000원 (-15%) | 129,000원 (-13%) |
| 6~10명 | 37,000원 (-25%) | 119,000원 (-20%) |
| 11~20명 | 32,000원 (-35%) | 99,000원 (-33%) |
| 21명+ | 협의 | 협의 |

---

## 7. 대시보드 뷰 설계

### 7.1 전체 대시보드 구조

```
/dashboard
  +-- SDMatrix          (S/D 매트릭스) [MVP-완료]
  +-- TopCompanies      (Top 20 채용 볼륨) [MVP-완료]
  +-- CompanyTimeline   (시계열 기업 채용 인텔리전스) [MVP-완료]
  +-- HiringTrends      (채용 트렌드) [MVP-완료]
  +-- ResumeMatch       (이력서 매칭) [MVP-완료]
  +-- CompanyAnalysis   (기업 분석) [MVP-완료]
```

사이드바 + 탑바 레이아웃. 각 뷰는 독립 컴포넌트로 lazy-load. React Router v7 기반 URL 라우팅.

### 7.2 View 1: S/D 매트릭스 (SDMatrix) [MVP-완료]

**차트 타입:** Bubble Chart (Recharts ScatterChart + custom bubble)

**축 정의:**

| 축 | 의미 | 데이터 소스 |
|---|---|---|
| X | 채용 수요 (주간 공고 수) | Wanted + LinkedIn + Saramin + JobKorea 합산 |
| Y | 인재 공급 (LinkedIn Recruiter 풀 사이즈) | LinkedIn Recruiter RPS |
| 버블 크기 | OTW% (Open to Work 비율) | LinkedIn Recruiter RPS |

**사분면 기준선:** X=1,400 (주간 공고 수), Y=10,500 (인재 풀 사이즈)

| 사분면 | 위치 | 의미 |
|---|---|---|
| 기회지대 | 우하단 (고수요/저공급) | 영업 타겟 우선순위 1순위 |
| 경쟁 시장 | 우상단 (고수요/고공급) | 표준 서치 |
| 과잉 공급 | 좌상단 (저수요/고공급) | 후보자 시장 우위 |
| 틈새 시장 | 좌하단 (저수요/저공급) | 전문 서치 가능 |

**Supply/Demand 뷰모드:** `viewMode` query parameter로 공급 관점/수요 관점 전환

```
/dashboard/sd-matrix?viewMode=supply  // 공급 관점 (기본)
/dashboard/sd-matrix?viewMode=demand  // 수요 관점
```

**인터랙션:**
- 버블 클릭 -> 하단 드릴다운 패널 (해당 세그먼트 Top 채용 기업 + 포지션) [백엔드 연동 필요]
- 범례 클릭 -> 동일 드릴다운

**Summary Metrics (헤더 카드 4개):** 전체 채용 공고, 기회지대 세그먼트 수, 평균 S/D Ratio, 최고 기회 세그먼트

### 7.3 View 2: Top 20 채용 볼륨 (TopCompanies) [MVP-완료]

**차트 타입:** Custom Horizontal Bar Ranking List (CSS-based)

```typescript
interface CompanyRankItem {
  companyId: string;            // UUID (추가)
  rank: number;
  company: string;
  segment: string;
  weeklyCount: number;
  positions: string[];
  weekOverWeekChange: number;
}
```

**인터랙션:** 행 클릭 -> 포지션 태그 accordion [백엔드 연동 필요]

### 7.4 View 3: 시계열 기업 채용 인텔리전스 (CompanyTimeline) [MVP-완료]

**세 가지 조회 모드:**

| 모드 | 설명 | 플랜 |
|---|---|---|
| Mode A: 총 채용 규모 | 기간 내 채용 공고 합산 Top N | Pro+ |
| Mode B: 단일 키워드 | 특정 직무/스킬 키워드 포함 Top N | Pro+ |
| Mode C: 복합 키워드 | AND/OR 조합 키워드 Top N | Enterprise |

Top N 범위: 20 / 50 / 100. 기간: 4주 / 8주 / 12주 / 26주 / 52주.

**시계열 차트:** 상위 5개 기업 개별 라인 + 나머지 그룹화 (회색 점선)

**영업 인텔리전스 시나리오:**
- 시나리오 1: Mode A 12주 Top 50 -> 지속 채용 기업 탐지 (영업 타겟)
- 시나리오 2: Mode B keyword="Kubernetes" 4주 Top 20 -> 인프라 전환 기업 탐지
- 시나리오 3: Mode C ["Java","MSA","결제"] AND 8주 Top 30 -> 후보자 배치처 탐색

### 7.5 View 4: 채용 트렌드 (HiringTrends) [MVP-완료]

**차트 타입:** Multi-line Chart (Recharts LineChart)

기본 표시: 최근 12주, 기본 5개 세그먼트. 범례 토글, 데이터 포인트 클릭 드릴다운 [백엔드 연동 필요]

### 7.6 View 5: 이력서 매칭 (ResumeMatch) [MVP-완료]

**이력서 매칭 입출력 스키마:**

```typescript
// Input
interface ResumeMatchInput {
  resumeText: string;            // 이력서 텍스트 (최대 10,000자)
  preferredSegments?: string[];  // 선호 세그먼트 필터
  minScore?: number;             // 최소 매칭 점수 (기본: 60)
  maxResults?: number;           // 최대 결과 수 (기본: 6, 최대: 20)
}

// Output
interface ResumeMatchOutput {
  matches: MatchResult[];
  extractedKeywords: string[];   // 이력서에서 추출한 키워드
  processingTimeMs: number;
  matchEngine: 'KEYWORD' | 'SEMANTIC';  // 사용된 엔진
}

interface MatchResult {
  companyId: string;             // UUID
  company: string;
  score: number;                 // 0-100
  segment: string;
  matchReason: string;           // 1-2문장 한국어 설명
  matchedSkills: string[];
  activePostings: number;
}
```

**MVP:** 키워드 기반 매칭 (클라이언트사이드) [MVP-완료]
**P6+:** Anthropic API (`claude-sonnet-4-20250514`) 시맨틱 매칭 [백엔드 연동 필요]

### 7.7 View 6: 기업 분석 (CompanyAnalysis) [MVP-완료]

**2-Panel 구조:** 인재 밀도 지수 (Talent Density Index) + 채용 파워 지수 (Hiring Power Index)

```typescript
interface CompanyProfile {
  companyId: string;             // UUID (추가)
  name: string;
  talentDensity: {
    overall: number;
    techDiversity: number;
    seniorRatio: number;
    avgTenure: string;
    internalOtwPct: number;
  };
  hiringPower: {
    overall: number;
    activePostings: number;
    weeklyTrend: number[];       // 12주 히스토리
  };
}
```

### 7.8 에러 바운더리 및 폴백 UI

모든 뷰에 React Error Boundary를 적용한다.

| 상태 | UI |
|---|---|
| 데이터 로딩 중 | Skeleton UI (뷰 구조 유지, 회색 플레이스홀더) |
| 데이터 없음 | EmptyState 컴포넌트 ("데이터가 아직 수집되지 않았습니다") |
| API 에러 (4xx) | 에러 메시지 카드 + 재시도 버튼 |
| API 에러 (5xx) | 에러 바운더리 폴백 ("일시적 오류, 잠시 후 다시 시도") |
| 네트워크 오프라인 | 캐시된 마지막 데이터 표시 + 오프라인 배너 |
| 권한 없음 | 잠금 오버레이 + 업그레이드 CTA |

---

## 8. 관리자 패널 (SuperAdmin)

### 8.1 유저 관리

**유저 목록:** 테이블 + 필터(카테고리, 요금제, 상태, 기간) + 검색(이름/이메일/회사명) + 페이지네이션(기본 20건, 50/100 선택)

**유저 상세:** 기본 정보 + 사용 통계(30일 API 추이, 기능 Top 5, 접속 히트맵) + 과금 정보 + 활동 로그

**유저 상태:** ACTIVE -> INACTIVE (90일 미접속) -> BLOCKED (SuperAdmin 차단) -> PENDING_DELETE (탈퇴 요청) -> DELETED (30일 유예 후)

### 8.2 트래픽 모니터링 및 이상 징후 탐지

**실시간 메트릭:** 동시 접속자, 금일 API 호출, 평균 응답시간, 미확인 알림 수

**이상 징후 탐지 규칙 (9개):**

| 규칙 ID | 조건 | 심각도 |
|---|---|---|
| TR-001 | RPM 300% 이상 증가 (1시간 대비) | WARNING |
| TR-002 | 단일 유저 분당 100회 이상 | CRITICAL |
| TR-003 | 순차적 Pagination 호출 + 짧은 간격 | WARNING |
| TR-004 | 엔드포인트 에러율 10% 초과 (5분) | WARNING |
| TR-005 | 5xx 에러 분당 50건 초과 | CRITICAL |
| TR-006 | 동일 IP 5분 내 로그인 실패 10회 | CRITICAL |
| TR-007 | 동일 계정 5개+ IP 동시 세션 | WARNING |
| TR-008 | 새벽 2-5시 평소 대비 500% 트래픽 | WARNING |
| TR-009 | 단일 유저 1시간 내 Export 10회+ | WARNING |

### 8.3 과금/빌링 관리

요금제 CRUD, 유저별 사용량 추적, 청구서 생성/관리(INV-YYYYMM-XXXXX), 할인/크레딧 관리

### 8.4 GA4 대시보드

DAU/WAU/MAU, 카테고리별 사용자 분포, 전환 퍼널 (방문 -> 가입 -> 첫 사용 -> 3개 뷰 사용 -> 유료 결제)

---

## 9. User 셀프서비스 대시보드

### 9.1 프로필 관리

프로필 이미지/이름/전화번호/소속회사/직무 수정, 이메일 변경(인증 플로우), 카테고리 변경 요청(SuperAdmin 승인)

### 9.2 결제 관리

현재 요금제 확인, 요금제 비교/변경(업그레이드: 즉시, 다운그레이드: 주기 종료 후), 결제 수단 관리(카드, 카카오페이, 네이버페이), 결제 이력/영수증

### 9.3 사용 분석

기능별 사용 횟수, 검색 히스토리, 활동 타임라인, API 사용량 현황

### 9.4 회원 탈퇴

30일 유예 기간, 활성 구독 선해지 필요, 탈퇴 사유 수집, 유예 기간 중 로그인 시 철회 가능

**데이터 보존 정책:**

| 데이터 유형 | 유예 기간 중 | 탈퇴 완료 후 | 법적 보존 |
|---|---|---|---|
| 계정 정보 | 보존 | 익명화 | 탈퇴 후 30일 |
| 결제 이력 | 보존 | 보존 | 5년 (전자상거래법) |
| 활동 로그 | 보존 | 익명화 | 3개월 (통신비밀보호법) |
| 프로필/설정/검색 | 보존 | 삭제 | - |

---

## 10. 기술 아키텍처

### 10.1 기술 스택

| 레이어 | 기술 | Phase | 비고 |
|---|---|---|---|
| **프론트엔드** | | | |
| UI Framework | React 19 | 기존 | [MVP-완료] |
| Language | TypeScript 5.9 | 기존 | [MVP-완료] |
| Build Tool | Vite 8 | 기존 | [MVP-완료] |
| Styling | Tailwind CSS 4 | 기존 | [MVP-완료] |
| Charts | Recharts 3 | 기존 | [MVP-완료] |
| Routing | React Router v7 | **Phase 1a** | [백엔드 연동 필요] |
| State Management | Zustand | **Phase 1a** | [백엔드 연동 필요] |
| Data Fetching | TanStack Query v5 | **Phase 1a** | Supabase 캐싱 + 실시간 |
| Form Handling | React Hook Form + Zod | **Phase 1a** | |
| HTTP Client | Axios | **Phase 1a** | JWT 인터셉터 |
| **백엔드** | | | |
| Framework | **FastAPI (Python)** | **Phase 1b** | NLP/ML 파이프라인 통합 유리 |
| ORM | SQLAlchemy 2.0 + Alembic | **Phase 1b** | |
| DB | Supabase (PostgreSQL 15) | 기존 설계 | RLS 활용 |
| Cache | Redis | Phase 2 | 세션, Rate Limit, API 캐시 |
| Search | Elasticsearch 8 | Phase 2 | 키워드 검색 + 자동완성 |
| **인프라** | | | |
| Hosting (FE) | Vercel | Phase 1a | |
| Hosting (BE) | Railway / Fly.io | Phase 1b | |
| CI/CD | GitHub Actions | Phase 1a | |
| Monitoring | Sentry + Grafana | Phase 1b | |
| Analytics | Google Analytics 4 | Phase 2 | |
| Payment | 토스페이먼츠 | Phase 2 | |

> **FastAPI 선택 근거 (Architect 피드백 반영):**
> - NLP 파이프라인(키워드 추출, 이력서 파싱)과 Python 에코시스템 직접 통합
> - Pydantic 기반 자동 OpenAPI 문서 생성
> - async/await 네이티브 지원으로 I/O 바운드 작업에 최적
> - 기존 Node.js/Next.js 없이 단일 언어(Python)로 백엔드 통합

### 10.2 React Router + TanStack Query (Phase 1a 배치)

> **Architect 피드백 반영:** React Router + TanStack Query는 Phase 3이 아닌 **Phase 1a**에서 도입한다. 이들은 인증/상태관리의 전제 조건이며, 나중에 도입하면 대규모 리팩토링이 필요하다.

**라우트 구조:**

```
/                              # 랜딩 (Guest)
/login                         # Google OAuth 로그인
/register                      # 회원가입 + 카테고리 선택

/dashboard                     # 메인 대시보드
/dashboard/sd-matrix           # S/D 매트릭스
/dashboard/top-companies       # Top 채용 볼륨
/dashboard/timeline            # 시계열 인텔리전스
/dashboard/trends              # 채용 트렌드
/dashboard/resume-match        # 이력서 매칭
/dashboard/company-analysis    # 기업 분석

/my                            # User 대시보드
/my/profile                    # 프로필
/my/billing                    # 결제 관리
/my/analytics                  # 사용 분석
/my/settings                   # 설정
/my/delete-account             # 탈퇴

/admin                         # SuperAdmin
/admin/users                   # 유저 관리
/admin/users/:id               # 유저 상세
/admin/traffic                 # 트래픽 모니터링
/admin/billing                 # 과금 관리
/admin/categories              # 카테고리 관리
/admin/ga                      # GA 대시보드
/admin/data                    # Raw 데이터 조회
```

**TanStack Query 활용:**

```typescript
// Supabase 실시간 구독 + 12주 캐싱
const { data: sdMatrix } = useQuery({
  queryKey: ['sd-matrix', week],
  queryFn: () => supabase.from('pulse.weekly_snapshots').select('*').eq('week', week),
  staleTime: 1000 * 60 * 60,  // 1시간
  gcTime: 1000 * 60 * 60 * 24, // 24시간
});
```

### 10.3 프론트엔드 아키텍처

```
Frontend (React 19 + Vite)
  +-- React Router v7 (라우팅)
  +-- Zustand Store (authStore, dashboardStore, adminStore, billingStore)
  +-- TanStack Query (서버 상태 관리 + 캐싱)
  +-- AuthGuard + RoleGuard (라우트 가드)
  +-- Pages (Public / Dashboard / My / Admin)
  +-- Services (AuthService, APIClient, GAService)
```

---

## 11. 데이터 모델

### 11.1 Supabase 스키마 매핑

```sql
-- auth 스키마 (Supabase Auth 내장)
auth.users                     -- Supabase Auth 관리

-- public 스키마 (앱 데이터)
public.organizations           -- 멀티 테넌시
public.organization_members    -- 조직-유저 매핑
public.user_profiles           -- 확장 프로필
public.subscriptions           -- 구독
public.invoices                -- 청구서
public.payment_methods         -- 결제 수단
public.activity_logs           -- 활동 로그
public.alerts                  -- 이상 징후 알림
public.traffic_logs            -- 트래픽 로그

-- pulse 스키마 (VXMI 전용)
pulse.job_postings             -- 주간 공고 수 (세그먼트 x 기업 x 플랫폼)
pulse.talent_pool              -- 인재 풀 사이즈 + OTW
pulse.weekly_snapshots         -- S/D ratio 주간 스냅샷
pulse.segment_snapshots        -- 세그먼트 시계열 (시계열 분석용)
pulse.keyword_index            -- 키워드 인덱스
pulse.candidate_scores         -- 후보자 스코어링 결과
pulse.retention_benchmark      -- Retention 벤치마크 (Enterprise)

-- ops 스키마 (공용)
ops.companies                  -- 기업 마스터 데이터
ops.positions                  -- 포지션 마스터

-- talent 스키마 (구직자)
talent.profiles                -- 이력서 + LinkedIn 연동
talent.market_position         -- 시장가치 스코어 시계열
talent.match_preferences       -- 관심 세그먼트 + 키워드 알림
talent.opt_in_pool             -- 매칭 풀 동의 유저

-- ti 스키마 (Talent Insight, Enterprise)
ti.overview                    -- LinkedIn Talent Insight 개요
ti.talent_flow_summary         -- 인재 흐름 요약
ti.talent_flow_detail          -- 인재 흐름 상세
ti.company_mapping             -- 기업 매핑
```

### 11.2 Company 타입 (companyId 추가)

> **Architect 피드백 반영:** 모든 Company 관련 타입에 `companyId: string` (UUID) 추가

```typescript
interface Company {
  companyId: string;             // UUID - PK
  name: string;
  normalizedName: string;        // 정규화된 기업명 (엔터티 해소용)
  segmentId: string;
  organizationId?: string;       // 멀티 테넌시 FK
  industry: string;
  size: 'STARTUP' | 'SME' | 'MID' | 'LARGE' | 'ENTERPRISE';
  createdAt: DateTime;
  updatedAt: DateTime;
}
```

### 11.3 week 필드 ISO 8601 형식

> **Architect 피드백 반영:** `week` 필드를 `YYYY-Www` ISO 8601 형식으로 통일

```typescript
// 기존: week: string  // 'YYYY-WW' 
// 변경: ISO 8601 week date format
type ISOWeek = string;  // 'YYYY-Www' (예: '2026-W12')

interface WeeklySnapshot {
  id: string;
  segmentId: string;
  week: ISOWeek;                 // ISO 8601: '2026-W12'
  demand: number;
  supply: number;
  sdRatio: number;
  otwPct: number;
  createdAt: DateTime;
}
```

### 11.4 segment_snapshots 시계열 테이블

> **Architect 피드백 반영:** 시계열 분석을 위한 세그먼트 스냅샷 테이블 설계

```sql
CREATE TABLE pulse.segment_snapshots (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  segment_id    TEXT NOT NULL,
  week          TEXT NOT NULL,           -- ISO 8601: 'YYYY-Www'
  demand        INTEGER NOT NULL,        -- 주간 공고 수
  supply        INTEGER NOT NULL,        -- 인재 풀 사이즈
  otw_pct       NUMERIC(5,2),            -- OTW 비율
  sd_ratio      NUMERIC(8,4),            -- S/D Ratio
  avg_salary    INTEGER,                 -- 평균 제시 연봉 (만원)
  top_companies JSONB,                   -- Top 5 기업 [{companyId, name, count}]
  metadata      JSONB,                   -- 확장 메타데이터
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(segment_id, week)
);

-- 인덱스
CREATE INDEX idx_segment_snapshots_week ON pulse.segment_snapshots(week);
CREATE INDEX idx_segment_snapshots_segment_week ON pulse.segment_snapshots(segment_id, week);

-- 52주 보존 후 아카이브 정책
-- CRON: DELETE FROM pulse.segment_snapshots WHERE week < (current_week - 104);
```

### 11.5 Organization 테이블

```sql
CREATE TABLE public.organizations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            VARCHAR(200) NOT NULL,
  type            VARCHAR(20) NOT NULL CHECK (type IN ('SEARCH_FIRM','CORPORATION','INDIVIDUAL')),
  plan            VARCHAR(20) NOT NULL DEFAULT 'STARTER',
  billing_email   VARCHAR(255) NOT NULL,
  max_seats       INTEGER NOT NULL DEFAULT 1,
  active_seats    INTEGER NOT NULL DEFAULT 0,
  settings        JSONB DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE public.organization_members (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  user_id         UUID NOT NULL REFERENCES auth.users(id),
  org_role        VARCHAR(10) NOT NULL DEFAULT 'MEMBER' CHECK (org_role IN ('OWNER','ADMIN','MEMBER')),
  joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  
  UNIQUE(organization_id, user_id)
);
```

### 11.6 User Profile 확장 테이블

```sql
CREATE TABLE public.user_profiles (
  id                UUID PRIMARY KEY REFERENCES auth.users(id),
  organization_id   UUID REFERENCES organizations(id),
  name              VARCHAR(100) NOT NULL,
  phone             VARCHAR(20),
  company           VARCHAR(200),
  job_title         VARCHAR(100),
  profile_image_url VARCHAR(500),
  role              VARCHAR(15) NOT NULL DEFAULT 'USER' CHECK (role IN ('SUPER_ADMIN','USER')),
  category          VARCHAR(20) NOT NULL CHECK (category IN ('JOB_SEEKER','INHOUSE_HR','HEADHUNTER','CHRO')),
  status            VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
  auth_provider     VARCHAR(10) NOT NULL DEFAULT 'GOOGLE',
  blocked_at        TIMESTAMPTZ,
  blocked_reason    TEXT,
  blocked_until     TIMESTAMPTZ,
  blocked_by        UUID REFERENCES auth.users(id),
  delete_requested_at TIMESTAMPTZ,
  delete_scheduled_at TIMESTAMPTZ,
  delete_reason     TEXT,
  last_login_at     TIMESTAMPTZ,
  login_count       INTEGER NOT NULL DEFAULT 0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS 정책
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile"
  ON public.user_profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "SuperAdmin can view all profiles"
  ON public.user_profiles FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.user_profiles
      WHERE id = auth.uid() AND role = 'SUPER_ADMIN'
    )
  );
```

---

## 12. API 설계

### 12.1 설계 원칙

| 원칙 | 상세 |
|---|---|
| RESTful | 리소스 기반 URL, HTTP 메서드 활용 |
| 버전 관리 | URL Prefix: `/api/v1/` |
| OpenAPI 3.1 | FastAPI 자동 생성, Swagger UI 제공 |
| 에러 형식 | RFC 7807 Problem Details |
| Rate Limiting | 역할별 차등, `X-RateLimit-*` 헤더 |

### 12.2 페이지네이션 (모든 List API 적용)

> **Architect 피드백 반영:** 모든 list API에 pagination 적용

**Offset 기반 (관리 화면):**

```
GET /api/v1/admin/users?page=1&limit=20&sort=-createdAt&filter[status]=ACTIVE&search=홍길동

Response:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalItems": 1532,
    "totalPages": 77
  }
}
```

**Cursor 기반 (대량 데이터, 시계열):**

```
GET /api/v1/dashboard/sd-matrix/snapshots?cursor=2026-W10&limit=12&direction=backward

Response:
{
  "data": [...],
  "pagination": {
    "cursor": "2026-W10",
    "nextCursor": "2025-W51",
    "hasMore": true,
    "limit": 12
  }
}
```

### 12.3 엔드포인트 설계

#### 인증 API

| Method | Endpoint | 설명 | Query Params |
|---|---|---|---|
| POST | `/api/v1/auth/google` | Google OAuth 로그인 (MVP) | - |
| POST | `/api/v1/auth/refresh` | Access Token 갱신 | - |
| POST | `/api/v1/auth/logout` | 로그아웃 | - |

> **MVP는 Google OAuth만 지원.** 이메일/비밀번호 인증은 Phase 2 이후.

#### 대시보드 API

| Method | Endpoint | 설명 | Query Params |
|---|---|---|---|
| GET | `/api/v1/dashboard/sd-matrix` | S/D 매트릭스 | `week`, `viewMode(supply\|demand)` |
| GET | `/api/v1/dashboard/sd-matrix/{segmentId}/drilldown` | 세그먼트 드릴다운 | `week`, `limit` |
| GET | `/api/v1/dashboard/companies` | 기업 랭킹 (통합) | `week`, `segmentId?`, `limit`, `cursor`, `sort` |
| GET | `/api/v1/dashboard/companies/{companyId}` | 기업 상세 | - |
| GET | `/api/v1/dashboard/companies/{companyId}/timeline` | 기업 시계열 | `weeks`, `segmentId?` |
| GET | `/api/v1/dashboard/timeline` | CompanyTimeline | `mode(A\|B\|C)`, `weeks`, `topN`, `segmentId?`, `keywords[]`, `operator(AND\|OR)` |
| GET | `/api/v1/dashboard/trends` | 채용 트렌드 | `weeks`, `segments[]`, `cursor` |
| GET | `/api/v1/dashboard/trends/{week}/{segmentId}/drilldown` | 트렌드 드릴다운 | `limit` |
| POST | `/api/v1/dashboard/resume-match` | 이력서 매칭 | - (Body: ResumeMatchInput) |
| GET | `/api/v1/dashboard/keywords/suggest` | 키워드 자동완성 | `q`, `limit` |

> **Architect 피드백 반영:** `companies/search`와 `companies/top`을 `/api/v1/dashboard/companies`로 통합. query params로 분기.

#### User API

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/v1/me/profile` | 내 프로필 |
| PATCH | `/api/v1/me/profile` | 프로필 수정 |
| GET | `/api/v1/me/subscription` | 내 구독 |
| PATCH | `/api/v1/me/subscription` | 요금제 변경 |
| DELETE | `/api/v1/me/subscription` | 구독 해지 |
| GET | `/api/v1/me/invoices` | 청구서 목록 (`page`, `limit`) |
| GET | `/api/v1/me/usage` | 사용량 통계 (`period`) |
| GET | `/api/v1/me/activity` | 활동 타임라인 (`page`, `limit`, `type?`) |
| POST | `/api/v1/me/delete-account` | 탈퇴 요청 |
| POST | `/api/v1/me/cancel-deletion` | 탈퇴 철회 |

#### SuperAdmin API

| Method | Endpoint | 설명 |
|---|---|---|
| GET | `/api/v1/admin/users` | 유저 목록 (`page`, `limit`, `sort`, `filter[*]`, `search`) |
| GET | `/api/v1/admin/users/{id}` | 유저 상세 |
| PATCH | `/api/v1/admin/users/{id}` | 유저 수정 |
| POST | `/api/v1/admin/users/{id}/block` | 차단 |
| POST | `/api/v1/admin/users/{id}/unblock` | 차단 해제 |
| GET | `/api/v1/admin/traffic/realtime` | 실시간 트래픽 |
| GET | `/api/v1/admin/alerts` | 알림 목록 (`page`, `limit`, `severity?`, `status?`) |
| PATCH | `/api/v1/admin/alerts/{id}` | 알림 상태 변경 |
| GET | `/api/v1/admin/organizations` | 조직 목록 (`page`, `limit`) |
| GET | `/api/v1/admin/revenue` | 매출 분석 (`period`) |

### 12.4 공통 에러 응답

```json
{
  "type": "https://valuehire.cc/errors/validation",
  "title": "Validation Error",
  "status": 400,
  "detail": "입력값이 올바르지 않습니다.",
  "errors": [
    { "field": "email", "message": "유효한 이메일 주소를 입력해주세요." }
  ]
}
```

| HTTP | Code | 설명 |
|---|---|---|
| 400 | VALIDATION_ERROR | 입력값 검증 실패 |
| 401 | UNAUTHORIZED / TOKEN_EXPIRED | 인증 필요 / 토큰 만료 |
| 403 | FORBIDDEN / PLAN_UPGRADE_REQUIRED | 권한 없음 / 요금제 업그레이드 필요 |
| 404 | NOT_FOUND | 리소스 없음 |
| 409 | CONFLICT | 중복 |
| 429 | RATE_LIMIT_EXCEEDED | API 한도 초과 |
| 500 | INTERNAL_ERROR | 서버 오류 |

---

## 13. 데이터 파이프라인

### 13.1 데이터 소스 및 수집

| 소스 | 수집 방법 | 주기 | 데이터 |
|---|---|---|---|
| Wanted | n8n 웹 스크래핑 | 주 1회 (월요일) | 채용 공고 |
| LinkedIn Jobs | n8n 웹 스크래핑 | 주 1회 (월요일) | 채용 공고 |
| Saramin | n8n 웹 스크래핑 | 주 1회 (월요일) | 채용 공고 |
| JobKorea | n8n 웹 스크래핑 | 주 1회 (월요일) | 채용 공고 |
| LinkedIn Recruiter | Claude in Chrome (수동) | 주 1회 | 인재 풀 사이즈, OTW |
| LinkedIn Talent Insights | Claude in Chrome (수동) | 월 1회 | 인재 흐름 (Enterprise) |
| 구직자 이력서 | 직접 업로드 (유저) | 실시간 | 이력서 + LinkedIn 프로필 |

### 13.2 LinkedIn 데이터 수집 제약

- 최대 30개 회사/세션
- 10개 회사당 30-60초 cooldown
- 자동화 탐지 회피 위해 인간 패턴 모방 필수
- Claude in Chrome 통한 반자동 수집

### 13.3 법적 리스크 (웹 스크래핑)

> **Architect + Critic 피드백 반영:** 데이터 소스별 법적 근거 및 리스크 분석

| 소스 | 법적 근거 | 리스크 수준 | 대응 |
|---|---|---|---|
| Wanted | 공개 채용 공고 (robots.txt 준수) | **낮음** | robots.txt 준수, rate limit 적용 |
| Saramin | 공개 채용 공고 (robots.txt 준수) | **낮음** | 위와 동일 |
| JobKorea | 공개 채용 공고 (robots.txt 준수) | **낮음** | 위와 동일 |
| LinkedIn Jobs | 공개 채용 공고 | **중간** | TOS 위반 가능성. 공개 데이터만 수집, 로그인 없이 접근 가능한 데이터만 |
| LinkedIn Recruiter | 라이선스 계약 하 수동 수집 | **중간** | Recruiter 라이선스 TOS 확인 필요. 대량 자동화 금지 |
| LinkedIn Talent Insights | 정식 라이선스 | **낮음** | 정식 구독 계약 |

**법률 자문 필요 사항:**
- 한국 부정경쟁방지법 상 데이터 스크래핑의 적법성 검토
- 각 플랫폼 TOS와의 충돌 여부 법률 의견서 확보
- 수집 데이터의 2차 가공 및 상업적 이용 적법성

### 13.4 데이터 소스 리스크 매트릭스

> **Critic 피드백 반영:** 데이터 소스별 리스크 + 폴백 + SLA

| 소스 | 차단 시 영향 | 폴백 전략 | 데이터 신선도 SLA |
|---|---|---|---|
| Wanted | S/D 매트릭스 정확도 하락 (~20%) | Saramin/JobKorea로 대체 보완 | 주 1회 (월요일 06:00 KST) |
| Saramin | 영향 낮음 (보조 소스) | Wanted + JobKorea로 충분 | 주 1회 (월요일 06:00 KST) |
| JobKorea | 영향 낮음 (보조 소스) | Wanted + Saramin으로 충분 | 주 1회 (월요일 06:00 KST) |
| LinkedIn Jobs | 글로벌 기업 채용 데이터 부재 | 글래스도어 등 대체 소스 탐색 | 주 1회 (월요일 06:00 KST) |
| LinkedIn Recruiter | 인재 풀 + OTW 데이터 부재 (치명적) | **대체 불가.** 수동 수집 지속 + 캐시 기반 운영 | 주 1회 (수동) |
| LinkedIn TI | Enterprise TI 기능 불가 | 해당 기능 일시 중단 안내 | 월 1회 (수동) |

### 13.5 기업명 정규화 (엔터티 해소)

> **Architect 피드백 반영:** 기업명 정규화 전략

```
문제: "삼성전자" / "Samsung Electronics" / "삼성전자(주)" / "SAMSUNG" → 동일 기업

전략:
1. 마스터 기업 DB (ops.companies) 구축: companyId + name + normalizedName + aliases[]
2. 수집 시 정규화 파이프라인:
   a. 전처리: 공백/특수문자 제거, (주)/(주식회사) 제거
   b. 한영 매핑 테이블 참조 (예: "삼성전자" <-> "Samsung Electronics")
   c. Fuzzy matching (Levenshtein distance < 3)
   d. 매칭 실패 시 -> pending_normalization 큐에 적재
   e. SuperAdmin 수동 확인 후 aliases에 추가
3. 주기적 품질 검증: 중복 기업 탐지 배치 (주 1회)
```

### 13.6 데이터 신선도 및 장애 처리

| 이벤트 | 감지 | 대응 |
|---|---|---|
| 스크래핑 실패 (단일 소스) | n8n 워크플로우 에러 알림 | 자동 재시도 3회, 실패 시 Slack 알림 |
| 스크래핑 실패 (전체) | 월요일 12:00까지 데이터 미갱신 | SuperAdmin 수동 트리거 + 사용자 공지 |
| 데이터 품질 이상 | 전주 대비 50% 이상 변동 | 자동 플래그 + SuperAdmin 검증 후 publish |
| LinkedIn 차단 | Recruiter 로그인 실패 / CAPTCHA | 수동 대응 + 차단 해제까지 캐시 데이터 |

---

## 14. 확장성 및 성능 전략

### 14.1 Materialized View / Pre-computation

> **Architect 피드백 반영:** 사전 계산 전략

| 뷰 | 사전 계산 대상 | 갱신 주기 | 저장 |
|---|---|---|---|
| S/D 매트릭스 | 14개 세그먼트 x 현재 주차 스냅샷 | 주 1회 (데이터 수집 후) | `pulse.weekly_snapshots` |
| Top 기업 랭킹 | 기업별 주간 합산 + WoW 변화율 | 주 1회 | Materialized View |
| 채용 트렌드 | 세그먼트별 12주 시계열 | 주 1회 | `pulse.segment_snapshots` |
| OppScore | 기업별 영업 기회 점수 | 주 1회 | Materialized View |

```sql
-- Materialized View 예시: Top 기업 랭킹
CREATE MATERIALIZED VIEW mv_company_rankings AS
SELECT
  c.id as company_id,
  c.name,
  c.segment_id,
  p.week,
  SUM(p.count) as weekly_total,
  RANK() OVER (PARTITION BY p.week ORDER BY SUM(p.count) DESC) as rank
FROM pulse.job_postings p
JOIN ops.companies c ON p.company_id = c.id
WHERE p.week >= (SELECT MAX(week) FROM pulse.job_postings) - interval '12 weeks'
GROUP BY c.id, c.name, c.segment_id, p.week;

-- 주 1회 갱신
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_company_rankings;
```

### 14.2 Elasticsearch 역할

> **Architect 피드백 반영:** Elasticsearch 역할 명확화

| 용도 | 상세 | Phase |
|---|---|---|
| **키워드 검색** | CompanyTimeline Mode B/C의 키워드 full-text 검색 | Phase 2 |
| **자동완성** | 키워드 입력 시 자동완성 (pulse.keyword_index 동기화) | Phase 2 |
| **기업명 검색** | 기업 분석 뷰 기업명 fuzzy search | Phase 2 |
| **이력서 매칭** | 키워드 기반 이력서-포지션 매칭 (시맨틱 매칭 이전) | Phase 3 |

> **Phase 1에서는 PostgreSQL ILIKE + trigram 인덱스로 대응.** Elasticsearch는 Phase 2에서 검색 품질/성능 한계 도달 시 도입.

### 14.3 캐싱 전략

| 계층 | 도구 | TTL | 대상 |
|---|---|---|---|
| 클라이언트 | TanStack Query | 1시간 | 대시보드 데이터 |
| CDN | Vercel Edge | 5분 | 정적 에셋 |
| API | Redis | 10분~1시간 | 비로그인 API, 공개 데이터 |
| DB | Materialized View | 주 1회 갱신 | 랭킹, 통계 |

---

## 15. 인증 및 보안

### 15.1 인증 (MVP: Google OAuth Only)

> **Architect 피드백 반영:** MVP는 Google OAuth만 지원. 이메일/비밀번호는 Phase 2 이후.

```
User -> "Google로 시작하기" -> Google OAuth 2.0 Authorization Code Flow
  -> Backend: Code -> Token 교환 -> 유저 정보 조회
  -> 기존 유저: JWT 발급 / 신규 유저: 자동 생성 + 카테고리 선택 후 JWT 발급
```

**JWT 설계:**

| 항목 | Access Token | Refresh Token |
|---|---|---|
| 알고리즘 | RS256 | - |
| 만료 | 15분 | 7일 (Remember Me: 30일) |
| Payload | `{sub, email, role, category, organizationId, plan}` | - |
| 저장 | 메모리 (Zustand) | HttpOnly Secure Cookie |
| 갱신 | - | Rotation (사용 시 새 토큰, 기존 무효화) |

### 15.2 보안 대책

| 영역 | 대책 |
|---|---|
| 인증 | JWT RS256, Refresh Token Rotation, HttpOnly Cookie |
| 인가 | RBAC 미들웨어, 프론트엔드 Guard + 백엔드 이중 검증 |
| XSS | React 기본 이스케이핑, CSP 헤더 |
| CSRF | SameSite Cookie, CSRF Token |
| SQL Injection | SQLAlchemy ORM (Parameterized Query) |
| Rate Limiting | 역할별 차등, IP + 유저 이중 제한 |
| 데이터 암호화 | HTTPS (TLS 1.3), DB 민감 정보 AES-256 |
| 세션 관리 | 동시 세션 제한, 비정상 세션 강제 종료 |
| 감사 로그 | 관리자 액션 전수 로깅 (append-only) |

---

## 16. 개인정보보호법(PIPA) 준수

### 16.1 적용 법률

| 법률 | 적용 범위 |
|---|---|
| 개인정보보호법 (PIPA) | 개인정보 수집/이용/제공 전반 |
| 정보통신망법 | 온라인 서비스 제공자의 개인정보 처리 |
| 전자상거래법 | 결제/거래 관련 데이터 보존 |
| 통신비밀보호법 | 통신 사실 확인 데이터 보존 |

### 16.2 개인정보 처리 원칙

| 원칙 | 적용 |
|---|---|
| 최소 수집 | Google OAuth 필수 정보만 수집 (이메일, 이름, 프로필 사진) |
| 목적 명시 | 서비스 제공, 맞춤 추천, 통계 분석 목적 명시 |
| 동의 기반 | 회원가입 시 개인정보 처리 동의, 마케팅 별도 동의 |
| 제3자 제공 | 구직자 데이터 -> 채용측 제공 시 별도 opt-in 동의 |
| 파기 | 탈퇴 시 30일 유예 후 삭제/익명화 |

### 16.3 데이터 보존 기간

| 데이터 | 보존 기간 | 근거 |
|---|---|---|
| 계정 정보 | 탈퇴 후 30일 | 개인정보보호법 |
| 결제 이력 | 5년 | 전자상거래법 제6조 |
| 접속 로그 | 3개월 | 통신비밀보호법 제15조의2 |
| 이력서 데이터 | 탈퇴 후 즉시 삭제 | 최소 보유 원칙 |
| 채용 시장 통계 | 영구 (익명화) | 통계 목적 |

### 16.4 개인정보영향평가 (PIA) 대상

- 구직자 이력서 처리 시스템
- LinkedIn 프로필 연동 시스템
- AI 기반 이력서 매칭 시스템 (Phase 3+)
- Cross-Track 데이터 연계 (Enterprise)

### 16.5 기술적 보호 조치

- 개인정보 DB 접근 로그 전수 기록
- 개인정보 포함 필드 암호화 (AES-256-GCM)
- 관리자 개인정보 조회 시 마스킹 기본 적용 (이름: 홍*동, 이메일: h***@example.com)
- 개인정보 Export 시 SuperAdmin 2인 승인 (Phase 3+)

---

## 17. 리스크 관리

### 17.1 데이터 소스 의존성 리스크

| 리스크 | 영향도 | 발생 확률 | 법적 근거 | 폴백 | 대응 |
|---|---|---|---|---|---|
| LinkedIn Recruiter 차단 | **치명적** | 중 | 라이선스 TOS | 대체 불가. 캐시 운영 | 수동 수집 다변화, 유료 API 전환 검토 |
| Wanted 스크래핑 차단 | 높음 | 낮음 | 공개 데이터 | Saramin+JobKorea 보완 | robots.txt 준수, rate limit |
| LinkedIn Jobs 차단 | 중간 | 중 | TOS 위반 가능 | 글래스도어 등 대체 | 공개 데이터만, 법률 검토 |
| 전체 소스 동시 장애 | 치명적 | 매우 낮음 | - | 마지막 캐시 데이터 표시 | 사용자 공지 + 수동 복구 |

### 17.2 기술 리스크

| 리스크 | 영향도 | 확률 | 대응 |
|---|---|---|---|
| React Router 전환 시 기존 뷰 이슈 | 중 | 중 | 단계적 마이그레이션 + E2E 테스트 선행 |
| PG사 결제 연동 지연 | 높 | 중 | Phase 1b에서 PG사 심사 신청 (2-4주 소요) |
| 실시간 트래픽 모니터링 성능 | 높 | 낮 | SSE/30초 폴링으로 시작, 필요 시 WebSocket 전환 |
| 대량 트래픽 로그 스토리지 | 중 | 높 | PostgreSQL 파티셔닝 -> TimescaleDB 전환 계획 |
| FastAPI 학습 곡선 | 중 | 중 | 팀 내 Python 경험자 확보, 공식 문서 기반 개발 |

### 17.3 비즈니스 리스크

| 리스크 | 영향도 | 확률 | 대응 |
|---|---|---|---|
| 유료 전환율 저조 | 높 | 중 | Free 기능 적절히 제한 + A/B 테스트 Paywall 최적화 |
| 개인정보보호법 위반 | 높 | 낮 | 법률 검토, PIA 실시, 최소 수집 원칙 |
| 스크래핑/데이터 탈취 | 높 | 중 | 다중 탐지 시그널 + Rate Limiting + 법적 대응 |
| 경쟁사 유사 서비스 | 중 | 중 | 차별화된 데이터 품질 + 카테고리 맞춤 기능 |

### 17.4 운영 리스크

| 리스크 | 영향도 | 확률 | 대응 |
|---|---|---|---|
| SuperAdmin 부재 시 긴급 대응 | 높 | 낮 | 최소 2명 SuperAdmin, 자동 대응 규칙, Slack 에스컬레이션 |
| 결제 장애 (PG사 다운) | 높 | 낮 | PG사 이중화, 자동 재시도 3회, 수동 결제 링크 |
| 데이터 유실 | 높 | 낮 | 일일 백업 + 실시간 레플리카. RTO < 1시간, RPO < 5분 |

---

## 18. 테스트 전략

### 18.1 테스트 피라미드

| 레벨 | 도구 | 커버리지 목표 | 대상 |
|---|---|---|---|
| **단위 테스트** | Vitest | 80%+ (비즈니스 로직) | 유틸 함수, 데이터 변환, 매칭 로직 |
| **컴포넌트 테스트** | Vitest + React Testing Library | 주요 컴포넌트 100% | MetricCard, DataTable, ChartWrapper, AuthGuard |
| **API 통합 테스트** | pytest + httpx | 전 엔드포인트 100% | FastAPI 엔드포인트, 인증 플로우, RBAC |
| **데이터 파이프라인 테스트** | pytest | 전 파이프라인 100% | 스크래핑 파서, 정규화, 적재 검증 |
| **E2E 테스트** | Playwright | 핵심 경로 100% | 로그인 -> 대시보드 -> 드릴다운, 결제 플로우 |

### 18.2 핵심 경로 E2E 시나리오

| 시나리오 | 설명 | 런치 기준 |
|---|---|---|
| E2E-001 | Google OAuth 로그인 -> 대시보드 진입 -> S/D 매트릭스 조회 | **필수** |
| E2E-002 | Guest 접근 -> 제한 데이터 확인 -> 로그인 유도 | **필수** |
| E2E-003 | User 프로필 수정 -> 저장 확인 | **필수** |
| E2E-004 | 요금제 변경 -> PG 결제 -> 구독 활성화 | **필수** |
| E2E-005 | SuperAdmin 유저 목록 -> 필터 -> 상세 -> 차단 | **필수** |
| E2E-006 | 이력서 매칭 입력 -> 결과 확인 | 권장 |
| E2E-007 | CompanyTimeline Mode B 키워드 검색 -> 결과 | 권장 |
| E2E-008 | 회원 탈퇴 플로우 (요청 -> 유예 -> 철회) | 권장 |

### 18.3 데이터 파이프라인 검증

| 검증 항목 | 방법 | 주기 |
|---|---|---|
| 스크래핑 데이터 건수 | 전주 대비 +/-30% 범위 체크 | 매 수집 후 |
| 기업명 정규화 매칭률 | 미매칭 건수 모니터링 | 주 1회 |
| S/D Ratio 합리성 | ratio 범위 0.01~10.0 체크 | 매 계산 후 |
| 중복 데이터 | 동일 기업+주차+소스 중복 탐지 | 매 적재 후 |

### 18.4 런치 기준 (Launch Criteria)

- [ ] E2E 핵심 경로 (E2E-001~005) 100% 통과
- [ ] API 통합 테스트 전 엔드포인트 통과
- [ ] Lighthouse Performance Score 85+
- [ ] 에러율 < 1% (스테이징 환경 24시간 모니터링)
- [ ] 보안 점검 완료 (OWASP Top 10 체크리스트)
- [ ] 개인정보처리방침 법률 검토 완료

---

## 19. 모니터링 및 옵저버빌리티

### 19.1 모니터링 스택

| 도구 | 역할 | Phase |
|---|---|---|
| **Sentry** | 에러 트래킹 (FE + BE) | Phase 1a |
| **Grafana + Prometheus** | 메트릭 대시보드 | Phase 1b |
| **Loki** | 로그 수집/검색 | Phase 1b |
| **Uptime Robot** | 가용성 모니터링 (외부) | Phase 1a |
| **Supabase Dashboard** | DB 성능 모니터링 | 기존 |

### 19.2 핵심 메트릭

| 카테고리 | 메트릭 | 임계값 (알림) |
|---|---|---|
| **가용성** | Uptime | < 99.9% (월간) |
| **성능** | API P50 응답시간 | > 200ms |
| **성능** | API P95 응답시간 | > 1,000ms |
| **성능** | FCP (First Contentful Paint) | > 1.5s |
| **에러** | 5xx 에러율 | > 0.5% |
| **에러** | Sentry 미해결 이슈 | > 10건 |
| **DB** | 커넥션 풀 사용률 | > 80% |
| **DB** | 슬로우 쿼리 (> 1s) | > 5건/시간 |
| **파이프라인** | 스크래핑 실패율 | > 0% |
| **비즈니스** | 로그인 성공률 | < 98% |

### 19.3 알림 채널

| 심각도 | 채널 | 응답 SLA |
|---|---|---|
| CRITICAL | Slack #ops-critical + PagerDuty | 15분 |
| WARNING | Slack #ops-alert | 1시간 |
| INFO | Grafana 대시보드 (조회) | 다음 업무일 |

### 19.4 로그 표준

```json
{
  "timestamp": "2026-03-20T14:30:00.000Z",
  "level": "ERROR",
  "service": "api",
  "traceId": "abc123",
  "userId": "user-uuid",
  "organizationId": "org-uuid",
  "method": "GET",
  "path": "/api/v1/dashboard/sd-matrix",
  "statusCode": 500,
  "responseTimeMs": 1234,
  "error": { "type": "DatabaseError", "message": "Connection timeout" }
}
```

---

## 20. GA4 이벤트 설계

### 20.1 커스텀 이벤트

**인증:** `sign_up`(method, category), `login`(method), `login_failed`(error_type), `logout`

**기능 사용:** `view_analysis`(view_name), `search`(search_term, result_count), `filter_apply`(filter_type), `data_export`(format, row_count), `resume_match`(match_count, top_score), `company_detail_view`(company_name), `drilldown_open`(source_view)

**결제:** `view_pricing`, `begin_checkout`(plan_id, value), `purchase`(plan_id, value, currency), `plan_upgrade`(from, to), `subscription_cancel`(plan_id, reason)

### 20.2 Custom Dimensions

| Dimension | Scope | 설명 |
|---|---|---|
| user_role | User | SuperAdmin / User / Guest |
| user_category | User | 구직자 / 인하우스HR / 헤드헌터 / CHRO |
| subscription_plan | User | Talent Free / Talent Plus / Starter / Pro / Enterprise |
| organization_name | User | 소속 조직명 |

### 20.3 전환 목표

| 목표 | 이벤트 | 우선순위 |
|---|---|---|
| 회원가입 완료 | sign_up | 높음 |
| 유료 결제 | purchase | 높음 |
| 요금제 업그레이드 | plan_upgrade | 높음 |
| 첫 분석 뷰 사용 | view_analysis (first) | 중간 |

---

## 21. 로드맵

### 21.1 Phase 1a: 프론트엔드 인프라 (4주)

> **Architect + Critic 피드백 반영:** Phase 1을 1a(인프라) + 1b(통합)로 분리. React Router + TanStack Query + 인증 상태를 Phase 1a로 이동.

| 태스크 | 설명 | 산출물 |
|---|---|---|
| React Router v7 전환 | useState 탭 -> URL 라우팅 | 라우트 설정, 기존 6개 뷰 마이그레이션 |
| Zustand 도입 | authStore, dashboardStore | 글로벌 상태 분리 |
| TanStack Query 도입 | 서버 상태 관리 + 캐싱 레이어 | API 훅, 캐시 정책 |
| Google OAuth 연동 | Supabase Auth + Google OAuth | 로그인/가입 페이지 |
| RBAC Route Guard | AuthGuard + RoleGuard | 역할별 접근 제어 |
| 레이아웃 전환 | 사이드바 + 탑바 | SideNav, TopBar |
| Sentry 연동 | 에러 트래킹 | Sentry 프로젝트 설정 |
| Playwright E2E 기본 | 핵심 경로 테스트 | E2E-001, 002 |

**완료 기준:**
- Google OAuth 로그인/가입 동작
- URL 기반 네비게이션 (6개 뷰 + 인증 페이지)
- SuperAdmin/User/Guest 역할별 메뉴 분리
- E2E-001, 002 통과

### 21.2 Phase 1b: 백엔드 통합 (4주)

| 태스크 | 설명 | 산출물 |
|---|---|---|
| FastAPI 프로젝트 셋업 | 프로젝트 구조, Alembic, Docker | 백엔드 보일러플레이트 |
| Supabase 스키마 마이그레이션 | pulse/ops/talent 스키마 생성 | DB 마이그레이션 파일 |
| 대시보드 API 구현 | S/D 매트릭스, Top 기업, 트렌드 | 6개 뷰 API 엔드포인트 |
| 멀티 테넌시 기반 | Organization 엔터티, RLS | 조직 기반 데이터 격리 |
| n8n 파이프라인 연결 | 스크래핑 -> Supabase 적재 | 첫 실 데이터 수집 |
| 기업명 정규화 | 마스터 DB + 정규화 파이프라인 | ops.companies 초기 데이터 |
| Grafana + Prometheus | 백엔드 메트릭 대시보드 | 모니터링 셋업 |
| API 통합 테스트 | pytest 전 엔드포인트 | 테스트 스위트 |

**완료 기준:**
- 6개 뷰가 실 데이터(Supabase)로 동작
- n8n 파이프라인 1회 이상 성공 수집
- API 통합 테스트 통과
- Grafana 대시보드 동작

### 21.3 Phase 2: 사용자 관리 + 과금 (8주)

| 태스크 | 기간 | 설명 |
|---|---|---|
| SuperAdmin 유저 관리 | 3주 | 목록/상세/차단/카테고리 |
| User 프로필/결제 | 2주 | 셀프서비스 대시보드 |
| 요금제 + PG 결제 | 3주 | 토스페이먼츠 연동, 구독 관리 |

### 21.4 Phase 3: 인텔리전스 고도화 (8주)

| 태스크 | 기간 | 설명 |
|---|---|---|
| CompanyTimeline Mode B/C | 3주 | Elasticsearch 도입, 키워드 검색 |
| 후보자 스코어링 (Bulk) | 2주 | Pro 기능 |
| 이력서 매칭 (서버) | 2주 | FastAPI NLP 파이프라인 |
| 구직자 Track (Talent) | 1주 | Talent Free/Plus, 이력서 게이트 |

### 21.5 Phase 4: Enterprise + 트래픽 (8주)

| 태스크 | 기간 | 설명 |
|---|---|---|
| 트래픽 모니터링 | 3주 | 실시간 대시보드, 이상 징후 탐지 |
| TDI + Retention 벤치마크 | 2주 | Enterprise 기능 |
| Talent Flow | 2주 | LinkedIn TI 연동 |
| GA4 대시보드 | 1주 | SuperAdmin GA 뷰 |

### 21.6 Phase 5: AI + 고도화 (8주)

| 태스크 | 기간 | 설명 |
|---|---|---|
| AI 시맨틱 매칭 | 3주 | Claude API, Enterprise |
| 채용 수요 예측 | 2주 | ML 파이프라인 |
| 성능 최적화 | 1주 | 번들 분석, 코드 스플리팅 |
| 통합 QA | 2주 | E2E, 부하, 보안 점검 |

### 21.7 전체 타임라인 요약

| Phase | 기간 | 주요 산출물 |
|---|---|---|
| **1a: FE 인프라** | 4주 (M1) | React Router, Zustand, TanStack Query, Google OAuth, RBAC |
| **1b: BE 통합** | 4주 (M2) | FastAPI, Supabase 스키마, n8n 파이프라인, 실 데이터 |
| **2: 사용자+과금** | 8주 (M3-4) | SuperAdmin, User 대시보드, PG 결제 |
| **3: 인텔리전스** | 8주 (M5-6) | Elasticsearch, Bulk 스코어링, 구직자 Track |
| **4: Enterprise** | 8주 (M7-8) | 트래픽 모니터링, TDI, Talent Flow |
| **5: AI+고도화** | 8주 (M9-10) | AI 매칭, 수요 예측, 성능 최적화 |

---

## 22. 팀 구성

> **Critic 피드백 반영:** 팀 규모 및 구성 명시

### 22.1 MVP 팀 (Phase 1a-1b, 2명)

| 역할 | 인원 | 담당 |
|---|---|---|
| 풀스택 리드 (Python/React) | 1명 | FastAPI 백엔드, React 프론트엔드, Supabase |
| 프로덕트 엔지니어 | 1명 | 대시보드 뷰, n8n 파이프라인, 데이터 수집 |

### 22.2 성장 팀 (Phase 2-3, 4명)

| 역할 | 인원 | 담당 |
|---|---|---|
| 풀스택 리드 | 1명 | 아키텍처, 코드 리뷰, 핵심 기능 |
| 백엔드 엔지니어 | 1명 | API, 데이터 파이프라인, Elasticsearch |
| 프론트엔드 엔지니어 | 1명 | 대시보드, Admin 패널, UX |
| 데이터 엔지니어 (파트타임) | 0.5명 | 스크래핑, NLP, ML 파이프라인 |

### 22.3 스케일업 팀 (Phase 4-5, 6명)

| 역할 | 추가 인원 | 담당 |
|---|---|---|
| + SRE / DevOps | 1명 | 인프라, 모니터링, 보안 |
| + ML 엔지니어 | 0.5명 | AI 매칭, 수요 예측 |

### 22.4 외부 리소스

| 역할 | 시기 | 목적 |
|---|---|---|
| 법률 자문 | Phase 1b | 스크래핑 적법성, 개인정보처리방침 |
| 디자인 (외주) | Phase 2 | 랜딩 페이지, 마케팅 에셋 |
| 보안 감사 | Phase 3 런칭 전 | OWASP Top 10, 침투 테스트 |

---

## 23. 성공 지표 (KPIs)

### 23.1 서비스 운영 KPI

| KPI | 목표 |
|---|---|
| 시스템 가용성 (Uptime) | 99.9% |
| API P50 / P95 응답시간 | < 100ms / < 500ms |
| FCP (First Contentful Paint) | < 1.5s |
| 에러율 (5xx) | < 0.1% |
| 로그인 성공률 | > 98% |
| 이상 징후 탐지율 | > 95% |
| 오탐율 (False Positive) | < 10% |

### 23.2 비즈니스 KPI

| KPI | 6개월 목표 | 12개월 목표 |
|---|---|---|
| **구직자 Track** | | |
| Talent Free 가입 (이력서 수) | 3,000 | 15,000 |
| Talent Free -> Plus 전환율 | 5% | 8% |
| Talent Plus MRR | 1,485,000원 (150명) | 11,880,000원 (1,200명) |
| **채용측 Track** | | |
| Starter 가입 | 500 | 2,000 |
| Starter -> Pro 전환율 | 8% | 12% |
| Pro -> Enterprise 전환율 | 5% | 10% |
| Pro MRR | 1,960,000원 (40명) | 11,760,000원 (240명) |
| Enterprise MRR | 1,490,000원 (10명) | 14,900,000원 (100명) |
| **전체** | | |
| Total MRR | 4,935,000원 | 38,540,000원 |
| Monthly Churn (B2B) | < 5% | < 3% |
| Monthly Churn (B2C) | < 8% | < 5% |
| NPS | 40+ | 50+ |
| DAU/MAU (Stickiness) | 25% | 30% |

---

## 24. 부록

### 24.1 14개 세그먼트 기준 데이터

```typescript
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
];
```

### 24.2 기존 프론트엔드 디렉토리 구조

```
vxmi-dashboard/src/
+-- App.tsx                     # 메인 앱 (탭 네비게이션) [Phase 1a에서 Router 전환]
+-- main.tsx
+-- index.css
+-- components/
|   +-- views/                  # 6개 분석 뷰 [MVP-완료]
|   |   +-- SDMatrixView.tsx
|   |   +-- TopCompaniesView.tsx
|   |   +-- CompanyTimelineView.tsx
|   |   +-- HiringTrendsView.tsx
|   |   +-- ResumeMatchView.tsx
|   |   +-- CompanyAnalysisView.tsx
|   +-- charts/
|   |   +-- TreeMapChart.tsx
|   +-- common/                 # 공통 컴포넌트 [MVP-완료]
+-- data/                       # Mock 데이터 [백엔드 연동 시 제거]
+-- types/
    +-- index.ts
```

### 24.3 Harness Feature List 매핑

| Feature ID | 뷰 | Phase | 상태 |
|---|---|---|---|
| `dashboard-shell` | 공통 레이아웃 | 1a | [MVP-완료] -> Router 전환 필요 |
| `sd-matrix-chart` | S/D 매트릭스 | 1a | [MVP-완료] |
| `sd-matrix-drilldown` | 드릴다운 | 1b | [백엔드 연동 필요] |
| `top-companies-list` | Top 20 랭킹 | 1a | [MVP-완료] |
| `company-timeline-shell` | 타임라인 셸 | 1a | [MVP-완료] |
| `company-timeline-mode-a` | 총 채용 규모 | 1b | [백엔드 연동 필요] |
| `company-timeline-mode-b` | 단일 키워드 | 3 | [백엔드 연동 필요] |
| `company-timeline-mode-c` | 복합 키워드 | 3 | [백엔드 연동 필요] |
| `hiring-trends-chart` | 트렌드 라인 | 1a | [MVP-완료] |
| `resume-match-keyword` | 키워드 매칭 | 1a | [MVP-완료] |
| `resume-match-semantic` | AI 매칭 | 5 | [백엔드 연동 필요] |
| `company-analysis-panel` | 기업 분석 | 1a | [MVP-완료] |
| `auth-google-oauth` | Google 인증 | 1a | [백엔드 연동 필요] |
| `rbac-route-guard` | 접근 제어 | 1a | [백엔드 연동 필요] |
| `admin-user-management` | 유저 관리 | 2 | [백엔드 연동 필요] |
| `billing-pg-integration` | PG 결제 | 2 | [백엔드 연동 필요] |
| `elasticsearch-search` | 키워드 검색 | 3 | [백엔드 연동 필요] |
| `traffic-monitoring` | 트래픽 모니터링 | 4 | [백엔드 연동 필요] |
| `ai-semantic-matching` | AI 시맨틱 매칭 | 5 | [백엔드 연동 필요] |

### 24.4 가격 산정 근거

| 항목 | 월 비용 (추정) |
|---|---|
| Supabase Pro | $25~$75 |
| LinkedIn Talent Insights | $8,000+ (연간, Enterprise 반영) |
| Anthropic API (Claude) | $50~$500 |
| Vercel/호스팅 | $20~$100 |
| Railway (FastAPI) | $20~$50 |
| n8n (자체 호스팅) | $24~$50 |
| Elasticsearch (Elastic Cloud) | $95~ (Phase 3 이후) |
| Sentry | $26/월 (Team) |
| Redis (Upstash) | $10~$30 |

### 24.5 관련 문서

| 문서 | 상태 | 비고 |
|---|---|---|
| `dashboard-design.md` | 참고 (본 PRD로 통합) | 뷰 설계 상세 |
| `VXMI-Pricing-Plan.md` v3 | 참고 (본 PRD로 통합) | 요금제/페르소나 상세 |
| `PRD-Admin-Panel.md` v1 | 참고 (본 PRD로 통합) | Admin 패널 상세 |
| API 서버 상세 설계 | 별도 작성 예정 | FastAPI OpenAPI spec |
| 디자인 시스템 가이드 | 별도 작성 예정 | 컴포넌트 라이브러리 |
| 개인정보처리방침 | 법무팀 협의 후 작성 | PIPA 준수 |

### 24.6 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|---|---|---|---|
| v1.0 | 2026-03-20 | Claude (Anthropic) | 초안 (3개 문서 기반) |
| v2.0 | 2026-03-20 | Claude (Anthropic) | Architect/Critic 피드백 반영 통합본. 멀티 테넌시, FastAPI, 법적 리스크, 테스트 전략, 모니터링, PIPA, 팀 구성, Phase 1a/1b 분리 추가. 용어 통일 (Pricing v3 기준). |

---

> **Architect/Critic 피드백 반영 체크리스트:**
>
> **Architect:**
> - [x] API 페이지네이션 (limit/offset/cursor) 모든 list API 적용 (섹션 12.2)
> - [x] 리소스 계층 통일, 중복 엔드포인트 제거 (섹션 12.3)
> - [x] companyId: string (UUID) 모든 Company 타입 (섹션 11.2)
> - [x] week 필드 ISO 8601 형식 (섹션 11.3)
> - [x] segment_snapshots 시계열 테이블 (섹션 11.4)
> - [x] 이력서 매칭 입출력 스키마 (섹션 7.6)
> - [x] FastAPI (Python) 백엔드 통합 (섹션 10.1)
> - [x] React Router + TanStack Query Phase 1 이동 (섹션 10.2, 21.1)
> - [x] 멀티 테넌시 (Organization, organization_id) (섹션 6)
> - [x] API-level 권한 매트릭스 (섹션 5.2)
> - [x] Google OAuth only MVP (섹션 15.1)
> - [x] 법적 리스크 (웹 스크래핑) (섹션 13.3)
> - [x] 엔터티 해소 전략 (기업명 정규화) (섹션 13.5)
> - [x] 데이터 신선도/장애 처리 (섹션 13.6)
> - [x] Materialized View 전략 (섹션 14.1)
> - [x] Elasticsearch 역할 명확화 (섹션 14.2)
> - [x] 테스트 전략 (섹션 18)
> - [x] 모니터링/옵저버빌리티 (섹션 19)
> - [x] 에러 바운더리/폴백 UI (섹션 7.8)
> - [x] PIPA 준수 (섹션 16)
> - [x] Phase 1a/1b 분리 (섹션 21.1, 21.2)
>
> **Critic:**
> - [x] 용어 통일 (Pricing v3 기준) (섹션 2)
> - [x] 단일 통합 PRD (본 문서)
> - [x] 데이터 소스 리스크 매트릭스 (법적 근거, 폴백, SLA) (섹션 13.4)
> - [x] 팀 구성 + Phase 1 범위 (섹션 22, 21)
> - [x] 테스트 전략 + E2E 런치 기준 (섹션 18)

---

*본 문서는 밸류커넥트 내부 문서입니다. 외부 유출을 금합니다.*
*v2.0 - 2026-03-20 | 작성: Claude (Anthropic) | 검토: TimSangmo*