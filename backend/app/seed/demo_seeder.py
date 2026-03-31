"""데모 데이터 시더 — B2B 프레젠테이션용 현실적 데이터 생성"""
import uuid
import random
import datetime
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.ops import Company, Position
from app.models.pulse import (
    JdAnalysis, CompanyDnaSnapshot, WeeklySnapshot,
    SegmentSnapshot, JobPosting
)
from app.constants.segments import SEGMENTS


# 데모 기업 정의 (현실적 한국 IT 기업)
DEMO_COMPANIES = [
    {"name": "토스", "industry": "핀테크", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "카카오", "industry": "플랫폼", "size": "enterprise", "primary_segment": "dev_server"},
    {"name": "네이버", "industry": "포털/AI", "size": "enterprise", "primary_segment": "dev_mlai"},
    {"name": "쿠팡", "industry": "이커머스", "size": "enterprise", "primary_segment": "dev_server"},
    {"name": "당근마켓", "industry": "로컬커머스", "size": "scale-up", "primary_segment": "dev_frontend"},
    {"name": "배달의민족", "industry": "푸드테크", "size": "enterprise", "primary_segment": "dev_server"},
    {"name": "라인", "industry": "메신저", "size": "enterprise", "primary_segment": "dev_frontend"},
    {"name": "크래프톤", "industry": "게임", "size": "enterprise", "primary_segment": "dev_server"},
    {"name": "하이퍼커넥트", "industry": "AI/소셜", "size": "scale-up", "primary_segment": "dev_mlai"},
    {"name": "비바리퍼블리카", "industry": "핀테크", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "야놀자", "industry": "여행/숙박", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "직방", "industry": "부동산", "size": "scale-up", "primary_segment": "dev_frontend"},
    {"name": "마켓컬리", "industry": "이커머스", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "뱅크샐러드", "industry": "핀테크", "size": "startup", "primary_segment": "dev_mlai"},
    {"name": "센드버드", "industry": "SaaS", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "리디", "industry": "콘텐츠", "size": "scale-up", "primary_segment": "dev_frontend"},
    {"name": "왓챠", "industry": "OTT", "size": "startup", "primary_segment": "dev_mlai"},
    {"name": "무신사", "industry": "패션", "size": "scale-up", "primary_segment": "dev_frontend"},
    {"name": "오늘의집", "industry": "인테리어", "size": "scale-up", "primary_segment": "dev_frontend"},
    {"name": "두나무", "industry": "핀테크/블록체인", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "스노우", "industry": "AI/카메라", "size": "scale-up", "primary_segment": "dev_mlai"},
    {"name": "버킷플레이스", "industry": "인테리어", "size": "startup", "primary_segment": "dev_frontend"},
    {"name": "클래스101", "industry": "에듀테크", "size": "startup", "primary_segment": "dev_frontend"},
    {"name": "그린랩스", "industry": "애그테크", "size": "startup", "primary_segment": "dev_server"},
    {"name": "원티드랩", "industry": "HR테크", "size": "scale-up", "primary_segment": "hr"},
    {"name": "채널코퍼레이션", "industry": "SaaS", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "스푼라디오", "industry": "오디오", "size": "startup", "primary_segment": "dev_frontend"},
    {"name": "데브시스터즈", "industry": "게임", "size": "scale-up", "primary_segment": "dev_server"},
    {"name": "마이리얼트립", "industry": "여행", "size": "startup", "primary_segment": "dev_server"},
    {"name": "숨고", "industry": "O2O", "size": "startup", "primary_segment": "dev_server"},
]

# 세그먼트별 현실적 기술 스택
TECH_BY_SEGMENT = {
    "dev_server": ["Java", "Spring Boot", "Python", "FastAPI", "Node.js", "Go", "Kotlin", "PostgreSQL", "Redis", "Kafka", "Docker", "Kubernetes", "AWS", "MySQL", "gRPC"],
    "dev_frontend": ["React", "TypeScript", "Next.js", "Vue.js", "JavaScript", "Tailwind CSS", "Redux", "GraphQL", "Webpack", "Storybook", "CSS", "HTML", "Figma"],
    "dev_mlai": ["Python", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "Spark", "Airflow", "MLflow", "Kubernetes", "CUDA", "Hugging Face", "LangChain"],
    "dev_devops": ["Kubernetes", "Docker", "Terraform", "AWS", "GCP", "Jenkins", "ArgoCD", "Prometheus", "Grafana", "Ansible", "Linux", "Bash", "Helm"],
    "dev_java": ["Java", "Spring Boot", "JPA", "Hibernate", "Gradle", "Maven", "Kafka", "Redis", "MySQL", "Oracle", "MSA", "Docker"],
    "dev_cto": ["Architecture", "System Design", "AWS", "Kubernetes", "Leadership", "Agile", "DevOps", "Security"],
    "dev_total": ["JavaScript", "Python", "Java", "React", "Node.js", "AWS", "Docker", "SQL", "Git", "TypeScript"],
    "design": ["Figma", "Sketch", "Adobe XD", "Photoshop", "Illustrator", "Framer", "Prototyping", "UX Research"],
    "pm_po": ["JIRA", "Confluence", "SQL", "Data Analysis", "A/B Testing", "Agile", "Scrum", "Product Strategy"],
    "marketing": ["Google Analytics", "SEO", "SEM", "Facebook Ads", "Content Marketing", "CRM", "SQL", "Python"],
    "hr": ["채용", "인사관리", "조직문화", "HRM", "성과관리", "보상설계", "노무", "HRIS"],
    "cfo_finance": ["재무분석", "회계", "SAP", "Excel", "SQL", "IR", "세무", "감사"],
    "sales": ["CRM", "Salesforce", "영업전략", "B2B", "파트너십", "협상", "프레젠테이션"],
    "strategy": ["전략기획", "시장분석", "재무모델링", "Excel", "PPT", "데이터분석", "컨설팅"],
}

# 세그먼트별 연봉 범위 (만원)
SALARY_RANGES = {
    "dev_server": (4000, 12000), "dev_frontend": (3500, 10000), "dev_mlai": (5000, 15000),
    "dev_devops": (4500, 12000), "dev_java": (4000, 11000), "dev_cto": (8000, 20000),
    "dev_total": (3000, 9000), "design": (3000, 8000), "pm_po": (4000, 10000),
    "marketing": (3000, 7000), "hr": (3000, 7000), "cfo_finance": (4000, 10000),
    "sales": (3000, 9000), "strategy": (4000, 10000),
}


class DemoSeeder:
    """데모 데이터 시더"""

    def __init__(self, db: Session):
        self.db = db

    def _generate_weeks(self, count: int = 12) -> list[str]:
        """최근 N주의 ISO week 문자열 생성"""
        now = datetime.datetime.now(datetime.UTC)
        weeks = []
        for i in range(count - 1, -1, -1):
            d = now - datetime.timedelta(weeks=i)
            iso = d.isocalendar()
            weeks.append(f"{iso[0]}-W{iso[1]:02d}")
        return weeks

    def _seed_companies(self) -> list[Company]:
        """데모 기업 30개 생성/업데이트"""
        companies = []
        for info in DEMO_COMPANIES:
            stmt = pg_insert(Company).values(
                id=uuid.uuid4(),
                name=info["name"],
                normalized_name=info["name"].lower().replace(" ", ""),
                segment_id=info["primary_segment"],
                industry=info["industry"],
                size=info["size"],
            ).on_conflict_do_update(
                index_elements=["normalized_name"],
                set_={"industry": info["industry"], "size": info["size"], "segment_id": info["primary_segment"]},
            ).returning(Company.id, Company.name, Company.segment_id)

            result = self.db.execute(stmt)
            row = result.fetchone()
            if row:
                c = Company(id=row.id, name=row.name, segment_id=row.segment_id)
                companies.append(c)

        self.db.flush()
        return companies

    def _seed_weekly_snapshots(self, weeks: list[str]) -> None:
        """시장 수준 주간 스냅샷 생성"""
        for week in weeks:
            for seg in SEGMENTS:
                sid = seg["id"]
                demand = random.randint(50, 300)
                supply = random.randint(30, 250)
                sd_ratio = round(demand / max(supply, 1), 4)
                otw_pct = round(random.uniform(5, 25), 2)

                stmt = pg_insert(WeeklySnapshot).values(
                    id=uuid.uuid4(),
                    segment_id=sid,
                    week=week,
                    demand=demand,
                    supply=supply,
                    sd_ratio=Decimal(str(sd_ratio)),
                    otw_pct=Decimal(str(otw_pct)),
                ).on_conflict_do_nothing()
                self.db.execute(stmt)
        self.db.flush()

    def _seed_job_postings_and_positions(self, companies: list, weeks: list[str]) -> None:
        """기업별 채용 공고 + 포지션 생성"""
        for company in companies:
            info = next((c for c in DEMO_COMPANIES if c["name"] == company.name), None)
            if not info:
                continue

            seg_id = info["primary_segment"]
            # 성장 트렌드: scale-up은 증가, enterprise는 안정, startup은 변동
            base_count = {"enterprise": 8, "scale-up": 5, "startup": 3}.get(info["size"], 4)

            for i, week in enumerate(weeks):
                # 트렌드 반영
                if info["size"] == "scale-up":
                    count = base_count + i // 3  # 점진적 증가
                elif info["size"] == "startup":
                    count = max(1, base_count + random.randint(-2, 3))  # 변동
                else:
                    count = base_count + random.randint(-1, 1)  # 안정

                # JobPosting 생성
                stmt = pg_insert(JobPosting).values(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    segment_id=seg_id,
                    week=week,
                    platform="wanted",
                    count=count,
                ).on_conflict_do_nothing()
                self.db.execute(stmt)

                # Position + JdAnalysis 생성 (count만큼)
                sal_range = SALARY_RANGES.get(seg_id, (3000, 8000))
                techs = TECH_BY_SEGMENT.get(seg_id, ["Python", "JavaScript"])

                for j in range(min(count, 3)):  # 최대 3개 position/week
                    pos_id = uuid.uuid4()
                    role_levels = ["junior", "mid", "senior", "lead"]
                    role_weights = [0.2, 0.35, 0.3, 0.15]
                    role = random.choices(role_levels, weights=role_weights, k=1)[0]
                    sal_min = random.randint(sal_range[0], sal_range[0] + (sal_range[1] - sal_range[0]) // 2)
                    sal_max = random.randint(sal_min, sal_range[1])

                    # Position
                    stmt = pg_insert(Position).values(
                        id=pos_id,
                        company_id=company.id,
                        title=f"{company.name} {seg_id} 개발자 {j+1}",
                        segment_id=seg_id,
                        week=week,
                        platform="wanted",
                        url=f"https://wanted.co.kr/wd/{random.randint(100000, 999999)}",
                        raw_text=f"[데모] {company.name}에서 {seg_id} 개발자를 모집합니다.",
                        salary_min=sal_min,
                        salary_max=sal_max,
                    ).on_conflict_do_nothing()
                    self.db.execute(stmt)

                    # JdAnalysis
                    selected_techs = random.sample(techs, min(random.randint(3, 8), len(techs)))
                    exp_min = {"junior": 0, "mid": 3, "senior": 5, "lead": 8}.get(role, 3)
                    exp_max = exp_min + random.randint(2, 5)
                    has_equity = random.random() < 0.4
                    benefits_pool = ["유연근무", "점심제공", "스톡옵션", "재택근무", "교육비지원", "건강검진", "장비지원", "자율출퇴근"]
                    benefits = random.sample(benefits_pool, random.randint(2, 5))
                    growth_stages = ["startup", "scale-up", "enterprise"]
                    growth_stage = info["size"] if info["size"] in growth_stages else "scale-up"

                    parsed_data = {
                        "tech_stack": selected_techs,
                        "experience": {"min_years": exp_min, "max_years": exp_max, "level": role},
                        "compensation": {
                            "salary_min": sal_min, "salary_max": sal_max,
                            "has_equity": has_equity, "benefits": benefits,
                        },
                        "role_keywords": [f"{seg_id} 개발", "설계", "코드리뷰"],
                        "domain_knowledge": [info["industry"]],
                        "org_signals": {
                            "team_size": f"{random.randint(5, 30)}명",
                            "is_new_position": random.random() < 0.5,
                            "growth_stage": growth_stage,
                        },
                    }

                    stmt = pg_insert(JdAnalysis).values(
                        id=uuid.uuid4(),
                        position_id=pos_id,
                        company_id=company.id,
                        segment_id=seg_id,
                        platform="wanted",
                        week=week,
                        parsed_data=parsed_data,
                        tech_stacks=selected_techs,
                        experience_min=exp_min,
                        experience_max=exp_max,
                        salary_min=sal_min,
                        salary_max=sal_max,
                        role_level=role,
                        domain_tags=[info["industry"]],
                        model_used="demo-seeder",
                        parsed_at=datetime.datetime.now(datetime.UTC),
                    ).on_conflict_do_nothing()
                    self.db.execute(stmt)

        self.db.flush()

    def _seed_dna_snapshots(self, companies: list, weeks: list[str]) -> None:
        """CompanyDnaService.refresh_all() 호출하여 DNA 스냅샷 생성"""
        from app.services.company_dna_service import CompanyDnaService
        dna_service = CompanyDnaService(self.db)
        for week in weeks:
            dna_service.refresh_all(week)

    def run(self, weeks: int = 12, companies_count: int = 30) -> dict:
        """데모 데이터 전체 시딩 실행"""
        week_list = self._generate_weeks(weeks)

        # 1. 기업 생성
        companies = self._seed_companies()

        # 2. 시장 스냅샷
        self._seed_weekly_snapshots(week_list)

        # 3. 채용 공고 + 포지션 + JD 분석
        self._seed_job_postings_and_positions(companies, week_list)

        # 4. DNA 스냅샷 (refresh_all 활용)
        self._seed_dna_snapshots(companies, week_list)

        self.db.commit()

        return {
            "companies_seeded": len(companies),
            "weeks": weeks,
            "week_range": f"{week_list[0]} ~ {week_list[-1]}",
            "status": "success",
        }
