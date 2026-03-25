"""기업명 정규화 스크립트

Usage:
    cd backend && python -m app.seed.normalize_companies
"""
import re
from collections import defaultdict
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.ops import Company
from app.models.pulse import JobPosting


# Canonical Korean name -> list of known aliases (Korean and English variants)
KNOWN_ALIASES: dict[str, list[str]] = {
    "삼성전자": ["Samsung Electronics", "삼성", "SAMSUNG", "Samsung"],
    "네이버": ["NAVER", "Naver Corp", "네이버(주)", "Naver"],
    "카카오": ["Kakao", "카카오(주)", "KAKAO"],
    "쿠팡": ["Coupang", "쿠팡(주)"],
    "토스(비바리퍼블리카)": ["Toss", "비바리퍼블리카", "Viva Republica", "토스"],
    "당근마켓": ["Danggeun Market", "당근", "Karrot", "당근(Karrot)"],
    "배달의민족(우아한형제들)": ["배민", "우아한형제들", "Woowa Brothers", "배달의민족"],
    "라인플러스": ["LINE Plus", "LINE", "라인"],
    "크래프톤": ["KRAFTON", "Krafton"],
    "엔씨소프트": ["NCSoft", "NCSOFT", "NC Soft"],
    "넷마블": ["Netmarble", "NETMARBLE"],
    "넥슨코리아": ["Nexon Korea", "NEXON", "Nexon"],
    "카카오뱅크": ["KakaoBank", "Kakao Bank"],
    "카카오페이": ["KakaoPay", "Kakao Pay"],
    "하이퍼커넥트": ["Hyperconnect", "HYPERCONNECT"],
    "무신사": ["Musinsa", "MUSINSA"],
    "직방": ["Zigbang", "ZIGBANG"],
    "야놀자": ["Yanolja", "YANOLJA"],
    "카카오모빌리티": ["Kakao Mobility"],
    "쏘카": ["SOCAR", "Socar"],
    "LG유플러스": ["LG U+", "LGU+"],
    "SK텔레콤": ["SKT", "SK Telecom"],
    "KT": [],
    "현대오토에버": ["Hyundai AutoEver"],
    "삼성SDS": ["Samsung SDS"],
    "LG CNS": ["LGCNS"],
    "SK C&C": [],
    "KB국민카드": ["KB Card", "KB국민"],
    "신한DS": ["Shinhan DS"],
    "카카오엔터프라이즈": ["Kakao Enterprise"],
    "네이버클라우드": ["Naver Cloud", "NCLOUD"],
    "위메프": ["WeMakePrice", "WEMAKEPRICE"],
    "11번가": ["11st", "11Street"],
    "지마켓": ["Gmarket", "GMARKET"],
    "올리브영": ["Olive Young", "CJ Olive Young"],
    "멜론컴퍼니": ["Melon", "Melon Company"],
    "NHN": [],
    "카카오게임즈": ["Kakao Games"],
    "스마일게이트": ["Smilegate", "SMILEGATE"],
    "펄어비스": ["Pearl Abyss"],
    "신세계아이앤씨": ["Shinsegae I&C"],
    "롯데정보통신": ["Lotte Information & Communications", "Lotte IT"],
    "리디": ["Ridibooks", "RIDI"],
    "원티드랩": ["Wanted Lab", "Wanted"],
    "잡코리아": ["JobKorea"],
    "사람인HR": ["Saramin", "사람인"],
    "그린랩스": ["Greenlabs", "GreenLabs"],
    "모두싸인": ["Modusign"],
}

# Suffixes to strip before comparison
SUFFIXES_TO_STRIP = [
    "(주)", "(株)", "Corp.", "Corp", "Inc.", "Inc",
    "Ltd.", "Ltd", "Co., Ltd.", "Co., Ltd", "Co.,Ltd",
    "Co.", "Co", "주식회사",
]


def _strip_suffixes(name: str) -> str:
    """Remove legal suffixes from a company name."""
    result = name.strip()
    changed = True
    while changed:
        changed = False
        for suffix in SUFFIXES_TO_STRIP:
            if result.endswith(suffix):
                result = result[: len(result) - len(suffix)].strip()
                changed = True
            if result.startswith("(주)"):
                result = result[3:].strip()
                changed = True
    return result


def normalize_company_name(name: str) -> str:
    """Return a cleaned, lowercased key suitable for dedup comparison.

    Steps:
    1. Strip leading/trailing whitespace
    2. Remove legal suffixes
    3. Collapse internal whitespace
    4. Lowercase
    """
    cleaned = _strip_suffixes(name)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.lower()


def find_canonical_name(name: str) -> tuple[str, list[str]]:
    """Return (canonical_name, aliases_list) for a given raw name.

    If the name matches a KNOWN_ALIASES key or one of its values,
    returns the canonical key.  Otherwise returns the cleaned name.
    """
    lower_name = normalize_company_name(name)

    for canonical, aliases in KNOWN_ALIASES.items():
        if normalize_company_name(canonical) == lower_name:
            return canonical, aliases
        for alias in aliases:
            if normalize_company_name(alias) == lower_name:
                return canonical, aliases

    # No known mapping — return stripped name as canonical
    cleaned = _strip_suffixes(name).strip()
    return cleaned, []


def _pick_winner(companies: list[Company]) -> Company:
    """Choose the record to keep when deduplicating.

    Heuristic: most non-null fields → largest aliases list → oldest record.
    """
    def score(c: Company) -> tuple[int, int]:
        non_null = sum(
            1 for v in [c.industry, c.size, c.segment_id, c.organization_id]
            if v is not None
        )
        alias_count = len(c.aliases) if c.aliases else 0
        return (non_null, alias_count)

    return max(companies, key=score)


def run_normalization() -> None:
    db: Session = SessionLocal()
    try:
        companies: list[Company] = db.query(Company).all()

        if not companies:
            print("No companies found in ops.companies — nothing to do.")
            return

        total = len(companies)
        print(f"Found {total} companies.")

        normalized_count = 0
        # Map normalized_name -> list of Company records
        groups: dict[str, list[Company]] = defaultdict(list)

        # Phase 1: compute canonical name + aliases for every row
        for company in companies:
            canonical, aliases = find_canonical_name(company.name)
            new_normalized = normalize_company_name(canonical)

            # Build merged alias list (deduplicated, excluding the canonical name itself)
            known_aliases = [a for a in aliases if a != canonical]
            existing_aliases: list[str] = company.aliases or []
            merged_aliases = list(
                dict.fromkeys(known_aliases + existing_aliases)
            )

            updated = False
            if company.normalized_name != new_normalized:
                company.normalized_name = new_normalized
                updated = True
            if company.aliases != merged_aliases:
                company.aliases = merged_aliases
                updated = True

            if updated:
                normalized_count += 1

            groups[new_normalized].append(company)

        db.flush()

        # Phase 2: deduplication
        duplicates_found = 0
        for norm_key, group in groups.items():
            if len(group) <= 1:
                continue

            duplicates_found += len(group) - 1
            winner = _pick_winner(group)
            losers = [c for c in group if c.id != winner.id]

            print(
                f"  Dedup '{norm_key}': keeping id={winner.id} "
                f"(name='{winner.name}'), removing {len(losers)} duplicate(s)."
            )

            for loser in losers:
                # Re-point pulse.job_postings to the winner
                affected = (
                    db.query(JobPosting)
                    .filter(JobPosting.company_id == loser.id)
                    .count()
                )
                if affected:
                    db.query(JobPosting).filter(
                        JobPosting.company_id == loser.id
                    ).update({"company_id": winner.id})
                    print(f"    Re-pointed {affected} job_postings from {loser.id} -> {winner.id}")

                # Merge aliases into winner
                loser_aliases: list[str] = loser.aliases or []
                winner_aliases: list[str] = winner.aliases or []
                merged = list(dict.fromkeys(winner_aliases + loser_aliases))
                if loser.name not in merged and loser.name != winner.name:
                    merged.append(loser.name)
                winner.aliases = merged

                db.delete(loser)

        db.commit()

        print("\n--- Normalization complete ---")
        print(f"  Total companies processed : {total}")
        print(f"  Rows updated (name/alias)  : {normalized_count}")
        print(f"  Duplicates removed         : {duplicates_found}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_normalization()
