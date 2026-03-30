# API Contract: VXMI Dashboard FE ↔ BE

## Conventions

### Naming
- All JSON request and response bodies use **camelCase** field names.
- Backend uses Pydantic `alias_generator` (`to_camel`) so snake_case fields are serialized as camelCase.

### Response Envelope (success)
```json
{
  "status": "success",
  "data": <T>,
  "message": null
}
```

### Error Envelope (RFC 7807 Problem Details)
```json
{
  "type": "about:blank",
  "title": "Human-readable summary",
  "status": 404,
  "detail": "Machine-readable explanation"
}
```

---

## Endpoints

### 1. GET /api/v1/dashboard/sd-matrix

Returns the supply/demand matrix for all segments and a summary.

**Query Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `week` | `string` | No | current week | ISO week string e.g. `2026-W12` |
| `viewMode` | `"supply" \| "demand"` | No | — | View mode hint for FE |

**Response**

```json
{
  "status": "success",
  "data": {
    "summary": {
      "totalPostings": 9900,
      "opportunitySegments": 5,
      "avgSDRatio": 1.35,
      "topOpportunitySegment": "ml-ai"
    },
    "segments": [
      {
        "segmentId": "frontend",
        "segmentName": "프론트엔드",
        "demand": 1820,
        "supply": 1340,
        "sdRatio": 1.36,
        "otwPct": 42.3,
        "quadrant": "COMPETITIVE",
        "avgSalary": 5800
      }
    ]
  }
}
```

**DashboardSummary DTO**

| Field | Type | Description |
|-------|------|-------------|
| `totalPostings` | `number` | Total job postings |
| `opportunitySegments` | `number` | Number of opportunity quadrant segments |
| `avgSDRatio` | `number` | Market-wide average S/D ratio |
| `topOpportunitySegment` | `string` | Segment ID with highest opportunity score |

**SDMatrixItem DTO**

| Field | Type | Description |
|-------|------|-------------|
| `segmentId` | `string` | Segment identifier |
| `segmentName` | `string` | Human-readable segment name |
| `demand` | `number` | Total demand (job postings) |
| `supply` | `number` | Total supply (candidates) |
| `sdRatio` | `number` | Supply/Demand ratio |
| `otwPct` | `number` | On-the-way percentage |
| `quadrant` | `"OPPORTUNITY" \| "COMPETITIVE" \| "OVERSUPPLY" \| "NICHE"` | Matrix quadrant |
| `avgSalary` | `number \| null` | Average salary (만원) |

---

### 2. GET /api/v1/dashboard/companies

Returns ranked list of companies by hiring activity.

**Query Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `week` | `string` | No | current week | ISO week string |
| `segmentId` | `string` | No | — | Filter by segment |
| `limit` | `number` | No | `20` | Max results (1–50) |

**Response**

```json
{
  "status": "success",
  "data": [
    {
      "companyId": "naver",
      "rank": 1,
      "company": "네이버",
      "segment": "backend",
      "weeklyCount": 72,
      "positions": ["백엔드", "DevOps"],
      "weekOverWeekChange": 5
    }
  ]
}
```

**CompanyRankItem DTO**

| Field | Type | Description |
|-------|------|-------------|
| `companyId` | `string` | Company identifier |
| `rank` | `number` | Current rank position |
| `company` | `string` | Company display name |
| `segment` | `string` | Primary segment |
| `weeklyCount` | `number` | Postings this week |
| `positions` | `string[]` | Active position titles |
| `weekOverWeekChange` | `number` | Week-over-week posting delta |

---

### 3. GET /api/v1/dashboard/timeline

Returns hiring timeline for companies over multiple weeks.

**Query Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `mode` | `"A" \| "B" \| "C"` | No | — | Timeline mode |
| `weeks` | `number` | No | `12` | Number of weeks to include |
| `topN` | `number` | No | — | Top N companies |
| `segmentId` | `string` | No | — | Filter by segment |
| `keywords[]` | `string[]` | No | — | Keyword filters |
| `operator` | `"AND" \| "OR"` | No | `"OR"` | Keyword operator |

**Response**

```json
{
  "status": "success",
  "data": [
    {
      "companyId": "naver",
      "company": "네이버",
      "data": [
        { "week": "2026-W11", "count": 42 },
        { "week": "2026-W12", "count": 55 }
      ]
    }
  ]
}
```

**CompanyTimeline DTO**

| Field | Type | Description |
|-------|------|-------------|
| `companyId` | `string` | Company identifier |
| `company` | `string` | Company display name |
| `data` | `TimelineDataPoint[]` | Weekly data points |

**TimelineDataPoint DTO**

| Field | Type | Description |
|-------|------|-------------|
| `week` | `string` | ISO week string |
| `count` | `number` | Posting count for that week |

---

### 4. GET /api/v1/dashboard/trends

Returns segment-level hiring trend over multiple weeks.

**Query Parameters**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `weeks` | `number` | No | `12` | Number of weeks |
| `segments` | `string` | No | — | Comma-separated segment IDs |

**Response**

```json
{
  "status": "success",
  "data": [
    {
      "segmentId": "backend",
      "segmentName": "백엔드",
      "data": [
        { "week": "2026-W11", "count": 2100 },
        { "week": "2026-W12", "count": 2150 }
      ]
    }
  ]
}
```

**SegmentTrend DTO**

| Field | Type | Description |
|-------|------|-------------|
| `segmentId` | `string` | Segment identifier |
| `segmentName` | `string` | Segment display name |
| `data` | `TrendDataPoint[]` | Weekly data points |

**TrendDataPoint DTO**

| Field | Type | Description |
|-------|------|-------------|
| `week` | `string` | ISO week string |
| `count` | `number` | Total posting count for that week |

---

### 5. POST /api/v1/dashboard/resume-match

Matches a resume against the company database and returns ranked results.

**Request Body**

```json
{
  "resumeText": "Python, FastAPI, React ...",
  "preferredSegments": ["backend", "fullstack"],
  "minScore": 0.6,
  "maxResults": 10
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `resumeText` | `string` | Yes | — | Raw resume text (min 10 chars) |
| `preferredSegments` | `string[]` | No | `[]` | Preferred segment IDs |
| `minScore` | `number` | No | `0.0` | Minimum match score (0–1) |
| `maxResults` | `number` | No | `10` | Maximum results to return |

**Response**

```json
{
  "status": "success",
  "data": {
    "matches": [
      {
        "companyId": "toss",
        "company": "토스",
        "score": 0.87,
        "segment": "backend",
        "matchReason": "핀테크 분야 적합",
        "matchedSkills": ["Python", "FastAPI"],
        "activePostings": 8
      }
    ],
    "extractedKeywords": ["Python", "FastAPI", "React"],
    "processingTimeMs": 142,
    "matchEngine": "KEYWORD"
  }
}
```

**ResumeMatchOutput DTO**

| Field | Type | Description |
|-------|------|-------------|
| `matches` | `MatchResult[]` | Ranked match results |
| `extractedKeywords` | `string[]` | Keywords extracted from resume |
| `processingTimeMs` | `number` | Processing duration in ms |
| `matchEngine` | `"KEYWORD" \| "SEMANTIC"` | Engine used |

**MatchResult DTO**

| Field | Type | Description |
|-------|------|-------------|
| `companyId` | `string` | Company identifier |
| `company` | `string` | Company display name |
| `score` | `number` | Match score 0.0–1.0 |
| `segment` | `string` | Matched segment |
| `matchReason` | `string` | Human-readable reason |
| `matchedSkills` | `string[]` | Skills matched |
| `activePostings` | `number` | Number of active postings |

---

### 6. GET /api/v1/dashboard/company-analysis/{companyId}

Returns deep analysis profile for a single company.

**Path Parameters**

| Name | Type | Description |
|------|------|-------------|
| `companyId` | `string` | Company identifier |

**Response**

```json
{
  "status": "success",
  "data": {
    "companyId": "kakao",
    "name": "카카오",
    "talentDensity": {
      "overall": 82,
      "techDiversity": 74,
      "seniorRatio": 38,
      "avgTenure": "3y2m",
      "internalOtwPct": 41.5
    },
    "hiringPower": {
      "overall": 91,
      "activePostings": 48,
      "weeklyTrend": [32, 38, 44, 48]
    }
  }
}
```

**CompanyProfile DTO**

| Field | Type | Description |
|-------|------|-------------|
| `companyId` | `string` | Company identifier |
| `name` | `string` | Company display name |
| `talentDensity` | `TalentDensity` | Talent composition metrics |
| `hiringPower` | `HiringPower` | Hiring strength metrics |

**TalentDensity DTO**

| Field | Type | Description |
|-------|------|-------------|
| `overall` | `number` | Overall talent density score (0–100) |
| `techDiversity` | `number` | Technology diversity score |
| `seniorRatio` | `number` | Senior engineer ratio (%) |
| `avgTenure` | `string` | Average employee tenure |
| `internalOtwPct` | `number` | Internal OTW percentage |

**HiringPower DTO**

| Field | Type | Description |
|-------|------|-------------|
| `overall` | `number` | Overall hiring power score (0–100) |
| `activePostings` | `number` | Current active postings |
| `weeklyTrend` | `number[]` | Weekly posting counts (recent 4 weeks) |

---

## Auth Endpoints

### POST /api/v1/auth/signup

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | `string` | Yes | Valid email address |
| `password` | `string` | Yes | Min 8 characters |
| `name` | `string` | No | Display name |
| `category` | `string` | No | `JOB_SEEKER \| INHOUSE_HR \| HEADHUNTER \| CHRO` |

### POST /api/v1/auth/signin

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | `string` | Yes | Registered email |
| `password` | `string` | Yes | Account password |

**Response**

```json
{
  "status": "success",
  "data": {
    "accessToken": "<jwt>",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "홍길동",
      "role": "USER",
      "category": "JOB_SEEKER",
      "plan": "TALENT_FREE",
      "track": "TALENT",
      "status": "ACTIVE",
      "authProvider": "EMAIL",
      "createdAt": "2026-01-01T00:00:00Z"
    }
  }
}
```

---

## PRO+ Endpoints

### GET /api/v1/dashboard/company-dna/{company_id}

**Auth**: PRO+
**Description**: 회사 DNA 프로필 — Tech/Hiring/Compensation/Culture 4축 분석

**Path Parameters**

| Name | Type | Description |
|------|------|-------------|
| `company_id` | `string` | Company identifier (UUID) |

**Response**

```json
{
  "status": "success",
  "data": {
    "companyId": "uuid",
    "companyName": "string",
    "segmentId": "string | null",
    "week": "2026-W13",
    "overallScore": 78.5,
    "tech": {
      "stackCount": 15,
      "diversityIndex": 3.2,
      "diversityScore": 75.0,
      "topTechs": [{"name": "Python", "count": 8, "pct": 53.3}]
    },
    "hiring": {
      "totalPostings": 42,
      "growthVelocity": 2.5,
      "growthLabel": "급성장",
      "intensityScore": 85.0,
      "roleDistribution": {"senior": 15, "mid": 20, "junior": 7},
      "segmentBreadth": 3
    },
    "compensation": {
      "salaryAvg": 6200,
      "salaryMin": 4000,
      "salaryMax": 10000,
      "positionPercentile": 75.0,
      "positionLabel": "상위 25%",
      "equityRatio": 0.8,
      "benefitsCount": 12,
      "topBenefits": ["유연근무", "점심제공", "스톡옵션"]
    },
    "culture": {
      "growthStage": "scale-up",
      "newPositionRatio": 0.6,
      "teamSizePatterns": ["10-15명", "12명"],
      "cultureScore": 72.0
    }
  }
}
```

**CompanyDnaProfile DTO**

| Field | Type | Description |
|-------|------|-------------|
| `companyId` | `string` | Company identifier (UUID) |
| `companyName` | `string` | Company display name |
| `segmentId` | `string \| null` | Primary segment ID |
| `week` | `string` | ISO week string |
| `overallScore` | `number` | Composite DNA score (0–100) |
| `tech` | `TechAxis` | Technology stack analysis |
| `hiring` | `HiringAxis` | Hiring intensity analysis |
| `compensation` | `CompensationAxis` | Compensation & benefits analysis |
| `culture` | `CultureAxis` | Culture & growth stage analysis |

**TechAxis DTO**

| Field | Type | Description |
|-------|------|-------------|
| `stackCount` | `number` | Total distinct tech stack items |
| `diversityIndex` | `number` | Shannon diversity index |
| `diversityScore` | `number` | Normalized diversity score (0–100) |
| `topTechs` | `TechItem[]` | Top technologies by frequency |

**HiringAxis DTO**

| Field | Type | Description |
|-------|------|-------------|
| `totalPostings` | `number` | Total active postings |
| `growthVelocity` | `number` | Week-over-week growth rate |
| `growthLabel` | `string` | Human-readable growth label (e.g. "급성장") |
| `intensityScore` | `number` | Hiring intensity score (0–100) |
| `roleDistribution` | `object` | Breakdown by seniority: `{senior, mid, junior}` |
| `segmentBreadth` | `number` | Number of segments hiring across |

**CompensationAxis DTO**

| Field | Type | Description |
|-------|------|-------------|
| `salaryAvg` | `number` | Average salary (만원) |
| `salaryMin` | `number` | Minimum salary (만원) |
| `salaryMax` | `number` | Maximum salary (만원) |
| `positionPercentile` | `number` | Percentile rank within segment |
| `positionLabel` | `string` | Human-readable percentile label |
| `equityRatio` | `number` | Ratio of postings mentioning equity |
| `benefitsCount` | `number` | Total distinct benefits offered |
| `topBenefits` | `string[]` | Most common benefit keywords |

**CultureAxis DTO**

| Field | Type | Description |
|-------|------|-------------|
| `growthStage` | `string` | Company growth stage (e.g. "scale-up", "startup") |
| `newPositionRatio` | `number` | Ratio of new vs. backfill positions |
| `teamSizePatterns` | `string[]` | Team size mentions extracted from JDs |
| `cultureScore` | `number` | Composite culture score (0–100) |

---

### GET /api/v1/dashboard/segment-benchmark/{segment_id}

**Auth**: PRO+
**Description**: 세그먼트 평균 DNA — 기업 DNA 비교 기준선

**Path Parameters**

| Name | Type | Description |
|------|------|-------------|
| `segment_id` | `string` | Segment identifier |

**Response**

```json
{
  "status": "success",
  "data": {
    "segmentId": "dev_server",
    "segmentName": "서버/백엔드",
    "avgTechScore": 62.0,
    "avgHiringScore": 55.0,
    "avgSalary": 5500,
    "avgCultureScore": 48.0,
    "companyCount": 35
  }
}
```

**SegmentBenchmark DTO**

| Field | Type | Description |
|-------|------|-------------|
| `segmentId` | `string` | Segment identifier |
| `segmentName` | `string` | Human-readable segment name |
| `avgTechScore` | `number` | Average tech diversity score (0–100) |
| `avgHiringScore` | `number` | Average hiring intensity score (0–100) |
| `avgSalary` | `number` | Average salary in segment (만원) |
| `avgCultureScore` | `number` | Average culture score (0–100) |
| `companyCount` | `number` | Number of companies in benchmark |
