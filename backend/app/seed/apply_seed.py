"""
실제 Supabase PostgreSQL DB에 시드 데이터 삽입 스크립트

실행 방법:
    cd backend && python -m app.seed.apply_seed
"""

import random
import uuid
from datetime import datetime, timedelta

from app.config import settings
from app.seed.dashboard_data import COMPANIES, SEGMENTS


def _get_week_labels(num_weeks: int = 12) -> list[str]:
    """최근 N주 ISO 주차 레이블 생성 (2026-W01 형식)"""
    today = datetime.now()
    weeks = []
    for i in range(num_weeks - 1, -1, -1):
        d = today - timedelta(weeks=i)
        year = d.isocalendar()[0]
        week = d.isocalendar()[1]
        weeks.append(f"{year}-W{week:02d}")
    return weeks


def seed_companies(db) -> dict[str, uuid.UUID]:
    """ops.companies 시드 데이터 삽입. 회사 id 문자열 -> UUID 매핑 반환."""
    from app.models.ops import Company

    print(f"  Seeding {len(COMPANIES)} companies...")

    # 기존 데이터 확인 (normalized_name 기준)
    existing_normalized = set()
    existing_rows = db.query(Company).all()
    for row in existing_rows:
        existing_normalized.add(row.normalized_name)

    company_id_map: dict[str, uuid.UUID] = {}

    # 기존 레코드도 id 맵에 포함
    for row in existing_rows:
        # COMPANIES 목록에서 매칭되는 id 찾기
        for c in COMPANIES:
            if c["name"].lower().strip() == row.normalized_name:
                company_id_map[c["id"]] = row.id
                break

    inserted = 0
    for company in COMPANIES:
        normalized = company["name"].lower().strip()
        if normalized in existing_normalized:
            continue

        new_id = uuid.uuid4()
        db.add(Company(
            id=new_id,
            name=company["name"],
            normalized_name=normalized,
            aliases=[],
            industry=company.get("industry"),
            size=company.get("size"),
        ))
        company_id_map[company["id"]] = new_id
        inserted += 1

    db.flush()
    print(f"    Inserted {inserted} new companies (skipped {len(COMPANIES) - inserted} existing)")
    return company_id_map


def seed_weekly_snapshots(db, weeks: list[str]) -> None:
    """pulse.weekly_snapshots 시드 데이터 삽입."""
    from app.models.pulse import WeeklySnapshot

    print(f"  Seeding weekly_snapshots ({len(SEGMENTS)} segments x {len(weeks)} weeks)...")

    # 기존 (segment_id, week) 조합 조회
    existing = set()
    for row in db.query(WeeklySnapshot.segment_id, WeeklySnapshot.week).all():
        existing.add((row.segment_id, row.week))

    inserted = 0
    for seg in SEGMENTS:
        for week in weeks:
            if (seg["id"], week) in existing:
                continue
            demand = random.randint(50, 500)
            supply = random.randint(30, 400)
            sd_ratio = round(demand / supply, 4) if supply > 0 else 1.0
            otw_pct = round(random.uniform(5, 25), 2)

            db.add(WeeklySnapshot(
                id=uuid.uuid4(),
                segment_id=seg["id"],
                week=week,
                demand=demand,
                supply=supply,
                sd_ratio=sd_ratio,
                otw_pct=otw_pct,
            ))
            inserted += 1

    db.flush()
    print(f"    Inserted {inserted} weekly_snapshots")


def seed_segment_snapshots(db, weeks: list[str]) -> None:
    """pulse.segment_snapshots 시드 데이터 삽입."""
    from app.models.pulse import SegmentSnapshot

    print(f"  Seeding segment_snapshots ({len(SEGMENTS)} segments x {len(weeks)} weeks)...")

    existing = set()
    for row in db.query(SegmentSnapshot.segment_id, SegmentSnapshot.week).all():
        existing.add((row.segment_id, row.week))

    inserted = 0
    for seg in SEGMENTS:
        for week in weeks:
            if (seg["id"], week) in existing:
                continue
            demand = random.randint(50, 500)
            supply = random.randint(30, 400)
            sd_ratio = round(demand / supply, 4) if supply > 0 else 1.0
            otw_pct = round(random.uniform(5, 25), 2)
            # avg_salary: 4000~12000 만원 단위 (* 10000)
            avg_salary = random.randint(4000, 12000) * 10000

            db.add(SegmentSnapshot(
                id=uuid.uuid4(),
                segment_id=seg["id"],
                week=week,
                demand=demand,
                supply=supply,
                sd_ratio=sd_ratio,
                otw_pct=otw_pct,
                avg_salary=avg_salary,
            ))
            inserted += 1

    db.flush()
    print(f"    Inserted {inserted} segment_snapshots")


def seed_job_postings(db, company_id_map: dict[str, uuid.UUID], weeks: list[str]) -> None:
    """pulse.job_postings 시드 데이터 삽입 (랜덤 company/segment/week 조합)."""
    from app.models.pulse import JobPosting

    # 기존 (company_id, segment_id, week) 조합 조회
    existing = set()
    for row in db.query(JobPosting.company_id, JobPosting.segment_id, JobPosting.week).all():
        existing.add((str(row.company_id), row.segment_id, row.week))

    company_keys = list(company_id_map.keys())
    segment_ids = [s["id"] for s in SEGMENTS]
    platforms = ["wanted", "jobkorea", "saramin", "linkedin", "jumpit"]

    # 각 week에 대해 랜덤 company+segment 조합 생성 (전체의 약 30%)
    target_combos = max(1, int(len(company_keys) * len(segment_ids) * 0.3))
    inserted = 0

    for week in weeks:
        combos_this_week = random.sample(
            [(c, s) for c in company_keys for s in segment_ids],
            k=min(target_combos, len(company_keys) * len(segment_ids)),
        )
        for company_key, segment_id in combos_this_week:
            company_uuid = company_id_map[company_key]
            key = (str(company_uuid), segment_id, week)
            if key in existing:
                continue
            db.add(JobPosting(
                id=uuid.uuid4(),
                company_id=company_uuid,
                segment_id=segment_id,
                platform=random.choice(platforms),
                week=week,
                count=random.randint(1, 20),
            ))
            existing.add(key)
            inserted += 1

    db.flush()
    print(f"    Inserted {inserted} job_postings")


def seed_talent_pool(db, weeks: list[str]) -> None:
    """pulse.talent_pool 시드 데이터 삽입."""
    from app.models.pulse import TalentPool

    print(f"  Seeding talent_pool ({len(SEGMENTS)} segments x {len(weeks)} weeks)...")

    # UniqueConstraint: (segment_id, week, source)
    existing = set()
    for row in db.query(TalentPool.segment_id, TalentPool.week, TalentPool.source).all():
        existing.add((row.segment_id, row.week, row.source))

    source = "seed"
    inserted = 0
    for seg in SEGMENTS:
        for week in weeks:
            if (seg["id"], week, source) in existing:
                continue
            pool_size = random.randint(100, 2000)
            otw_pct = round(random.uniform(5, 25), 2)
            otw_count = int(pool_size * otw_pct / 100)

            db.add(TalentPool(
                id=uuid.uuid4(),
                segment_id=seg["id"],
                week=week,
                pool_size=pool_size,
                otw_count=otw_count,
                otw_pct=otw_pct,
                source=source,
            ))
            inserted += 1

    db.flush()
    print(f"    Inserted {inserted} talent_pool rows")


def run_seed() -> None:
    """전체 시드 실행 진입점."""
    if not settings.DATABASE_URL:
        print("ERROR: DATABASE_URL이 설정되지 않았습니다.")
        print("  backend/.env 파일에 DATABASE_URL을 설정하세요.")
        return

    from app.database import SessionLocal
    if SessionLocal is None:
        print("ERROR: DB 세션을 초기화할 수 없습니다. DATABASE_URL을 확인하세요.")
        return

    weeks = _get_week_labels(12)
    print(f"Seed weeks: {weeks[0]} ~ {weeks[-1]}")
    print("Starting seed...")

    db = SessionLocal()
    try:
        print("\n[1/5] ops.companies")
        company_id_map = seed_companies(db)

        print("\n[2/5] pulse.weekly_snapshots")
        seed_weekly_snapshots(db, weeks)

        print("\n[3/5] pulse.segment_snapshots")
        seed_segment_snapshots(db, weeks)

        print("\n[4/5] pulse.job_postings")
        seed_job_postings(db, company_id_map, weeks)

        print("\n[5/5] pulse.talent_pool")
        seed_talent_pool(db, weeks)

        db.commit()
        print("\nSeed completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"\nERROR: Seed failed — {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
