"""
experience_parser.py
--------------------
Parses raw LinkedIn experience text (manually copied) into structured job records.

Each profile's 'experience' column contains a multiline block with all jobs.
This module segments that block into individual jobs and extracts:
  - job_title
  - company
  - employment_type
  - start_year / end_year (int or None for 'Present')
  - start_month / end_month (int or None)
  - duration_months (int)
  - is_current (bool)
  - location
  - work_mode (Remote / Hybrid / On-site)
  - seniority_hint (keyword-based label, before AI classification)
  - position_in_career (1 = most recent; useful for trajectory analysis)

Usage:
    from src.parsing.experience_parser import parse_profiles
    df_jobs = parse_profiles("data/raw/raw_profiles.csv")
    df_jobs.to_csv("data/processed/parsed_jobs.csv", index=False)
"""

import re
import pandas as pd
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

MONTH_ABBR = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

# Seniority keyword groups (order matters — more specific first)
SENIORITY_KEYWORDS = {
    "c_level":   r"\b(CEO|CTO|CFO|COO|CPO|CIO|CHRO|Chief)\b",
    "director":  r"\b(Director|VP|Vice\s*President|Head\s*of|Principal)\b",
    "manager":   r"\b(Manager|Lead|Team\s*Lead|Tech\s*Lead|Engineering\s*Lead|Founder|Co-Founder)\b",
    "senior":    r"\b(Senior|Sr\.?|Staff)\b",
    "mid":       r"\b(Engineer|Developer|Analyst|Designer|Consultant|Architect|Specialist)\b",
    "junior":    r"\b(Junior|Jr\.?|Graduate|Intern|Trainee|Apprentice|Student)\b",
}

EMPLOYMENT_TYPES = [
    "Full-time", "Part-time", "Self-Employed", "Contract",
    "Freelance", "Internship", "Freelance",
]
WORK_MODES = ["Remote", "Hybrid", "On-site"]

# ── Compiled Regexes ─────────────────────────────────────────────────────────

# Matches: "Jan 2019 - Present · 7 yrs 2 mos" or "2013 - Mar 2017 · 4 yrs"
# Also handles "to" as separator (LinkedIn copy-paste artefact of the second copy)
DATE_RANGE_RE = re.compile(
    r"(?P<start>" + MONTH_ABBR + r"\s+\d{4}|\d{4})"
    r"\s*(?:-|to)\s*"
    r"(?P<end>Present|" + MONTH_ABBR + r"\s+\d{4}|\d{4})"
    r"(?:\s*[·,]\s*(?P<duration>[^\n\r·]+))?",
    re.IGNORECASE,
)

# "Full-time · 11 yrs 3 mos"  — company-level group header, NOT a single job
COMPANY_GROUP_HEADER_RE = re.compile(
    r"^(?:Full-time|Part-time|Self-Employed|Contract|Freelance|Internship)"
    r"\s*·\s*\d",
    re.IGNORECASE,
)

DURATION_RE = re.compile(
    r"(?:(\d+)\s*yr[s]?)?\s*(?:(\d+)\s*mo[s]?)?", re.IGNORECASE
)

EMPLOYMENT_TYPE_RE = re.compile(
    r"\b(" + "|".join(EMPLOYMENT_TYPES) + r")\b", re.IGNORECASE
)

WORK_MODE_RE = re.compile(
    r"\b(" + "|".join(WORK_MODES) + r")\b", re.IGNORECASE
)

# Exact-match bare work-mode token (no surrounding text)
WORKMODE_ONLY_RE = re.compile(r"^(?:Remote|Hybrid|On-site)$", re.IGNORECASE)

# Lines that look like a geographic location
# e.g. "Bucharest, Romania · Hybrid", "Brasília, Distrito Federal, Brazil"
LOCATION_LINE_RE = re.compile(
    r"^[\w\s\-áéíóúàèìòùâêîôûäëïöüñçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÑÇ]+(,\s*[\w\s\-áéíóúàèìòùâêîôûäëïöüñçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÑÇ]+)+(\s*[·]\s*.*)?",
    re.UNICODE,
)
# Lines that are clearly location / metadata, not titles
SKIP_LINE_RE = re.compile(
    r"^("
    r"\d{4}"                            # bare year
    r"|" + MONTH_ABBR + r"\s+\d{4}"    # "Jan 2019"
    r"|\d+\s*yr[s]?.*"                  # "7 yrs 2 mos"
    r"|(?:Full-time|Part-time|Self-Employed|Contract|Freelance)$"  # bare type (Internship is a valid title)
    r")",
    re.IGNORECASE,
)


# ── Text Cleaning Helpers ────────────────────────────────────────────────────

def _deduplicate_concat(line: str) -> str:
    """
    Remove exact concatenated duplication on a single line.
    E.g. 'Oracle · Full-timeOracle · Full-time' → 'Oracle · Full-time'
    Handles even-length strings where both halves are identical.
    """
    s = line.strip()
    n = len(s)
    if n < 4 or n % 2 != 0:
        return s
    half = n // 2
    if s[:half] == s[half:]:
        return s[:half].strip()
    return s


def _is_location_line(line: str) -> bool:
    """
    Heuristically detect whether a line is a geographic location / work-mode
    metadata line rather than a job title or company name.

    Positive signals:
    - Contains a work mode keyword (Remote, Hybrid, On-site)
    - Looks like "City, Region" or "City, Country" (comma-separated place names)
    """
    if WORK_MODE_RE.search(line):
        return True
    # Comma-separated → likely a location ("Bucharest, Romania", "Brasília, D.F., Brazil")
    # Guard against company names with commas by checking that all parts look
    # like place tokens (no camelCase, no acronyms beyond 2 chars)
    parts = [p.strip() for p in line.split(",") if p.strip()]
    if len(parts) >= 2:
        # Reject if any part contains digits (addresses) or looks like a org name
        looks_like_place = all(
            re.match(r"^[\w\s\-\.áéíóúàèìòùâêîôûäëïöüñçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÑÇ]+$", p, re.UNICODE)
            for p in parts
        )
        if looks_like_place:
            return True
    return False


def _clean_lines(text: str) -> list[str]:
    """
    Split experience block into clean, deduplicated lines.
    - Strips leading/trailing whitespace (including indented title lines)
    - Deduplicates concatenated lines ('XY XY' → 'X')
    - Removes consecutive identical lines
    - Drops empty lines
    """
    raw_lines = text.split("\n")
    cleaned: list[str] = []
    for raw in raw_lines:
        line = _deduplicate_concat(raw.strip())  # .strip() handles leading spaces
        if not line:
            continue
        # Skip consecutive duplicate lines (LinkedIn renders title twice)
        if cleaned and cleaned[-1] == line:
            continue
        cleaned.append(line)
    return cleaned


# ── Duration Helpers ─────────────────────────────────────────────────────────

def _parse_duration_str(duration_str: Optional[str]) -> Optional[int]:
    """
    Convert a duration string to total months.
    '7 yrs 2 mos' → 86,  '10 mos' → 10,  '1 yr' → 12
    Returns None if unparseable.
    """
    if not duration_str:
        return None
    m = DURATION_RE.match(duration_str.strip())
    if not m:
        return None
    years = int(m.group(1)) if m.group(1) else 0
    months = int(m.group(2)) if m.group(2) else 0
    total = years * 12 + months
    return total if total > 0 else None


def _parse_year_month(date_str: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse a date token like 'Jan 2019' or '2019' into (year, month).
    Returns (year, None) for bare years.
    """
    date_str = date_str.strip()
    # "Jan 2019"
    parts = date_str.split()
    if len(parts) == 2:
        month_name, year_str = parts
        return int(year_str), MONTH_MAP.get(month_name.capitalize())
    # bare year "2019"
    if re.match(r"^\d{4}$", date_str):
        return int(date_str), None
    return None, None


# ── Seniority Classification (keyword-based) ─────────────────────────────────

def _infer_seniority(title: str) -> str:
    """
    Assign a coarse seniority label from the job title using keyword matching.
    Intended as a preliminary label before AI-based classification.

    Returns one of: 'c_level', 'director', 'manager', 'senior', 'mid', 'junior', 'unknown'
    """
    for level, pattern in SENIORITY_KEYWORDS.items():
        if re.search(pattern, title, re.IGNORECASE):
            return level
    return "unknown"


# ── Core Segmentation Logic ──────────────────────────────────────────────────

def _segment_jobs(lines: list[str]) -> list[dict]:
    """
    Identify individual job entries within a list of cleaned lines.

    Strategy: date-range lines are the most reliable structural anchor.
    Two-pass approach:
      Pass 1 – compute context_after for every job so we know exactly which
               lines have been "consumed" as metadata trailing each date.
      Pass 2 – compute context_before starting only AFTER the previous job's
               context_after, preventing location lines from bleeding forward.

    Returns a list of raw job dicts before field extraction.
    """
    # ── Pass 0: collect all date-range anchor lines ───────────────────────────
    date_hits: list[tuple[int, re.Match]] = []
    for i, line in enumerate(lines):
        m = DATE_RANGE_RE.search(line)
        if m and not COMPANY_GROUP_HEADER_RE.match(line):
            date_hits.append((i, m))

    if not date_hits:
        return []

    # ── Pass 1: compute context_after end-index for each job ─────────────────
    # context_after = lines following the date holding location / work-mode info.
    # STRICT: only consume a line if it is clearly a location or work-mode line.
    # This prevents title/company lines of the next job from being marked as
    # "consumed" and subsequently excluded from that job's context_before.

    after_end_indices: list[int] = []
    for rank, (date_idx, _) in enumerate(date_hits):
        next_anchor = (
            date_hits[rank + 1][0] if rank + 1 < len(date_hits) else len(lines)
        )
        end = date_idx  # default: only date line itself is consumed
        for j in range(date_idx + 1, min(date_idx + 3, next_anchor)):
            line = lines[j]
            if DATE_RANGE_RE.search(line):
                break
            # Only mark as consumed if the line is clearly location metadata
            if _is_location_line(line) or WORKMODE_ONLY_RE.match(line):
                end = j
            else:
                break  # first non-location line → stop consuming
        after_end_indices.append(end)

    # ── Pass 2: build each job record ────────────────────────────────────────
    jobs = []
    for rank, (date_idx, date_match) in enumerate(date_hits):
        # Lower bound: start AFTER the previous job's consumed context_after
        lower_bound = after_end_indices[rank - 1] + 1 if rank > 0 else 0

        # ── context_before: title + company ──────────────────────────────────
        context_before: list[str] = []
        for j in range(max(lower_bound, date_idx - 3), date_idx):
            line = lines[j]
            if SKIP_LINE_RE.match(line):
                continue
            if DATE_RANGE_RE.search(line):
                continue
            if COMPANY_GROUP_HEADER_RE.match(line):
                continue
            if _is_location_line(line):
                continue
            context_before.append(line)

        # ── context_after: location + work mode (strict: metadata lines only) ──
        next_anchor = (
            date_hits[rank + 1][0] if rank + 1 < len(date_hits) else len(lines)
        )
        context_after: list[str] = []
        for j in range(date_idx + 1, min(date_idx + 3, next_anchor)):
            line = lines[j]
            if DATE_RANGE_RE.search(line):
                break
            if _is_location_line(line) or WORKMODE_ONLY_RE.match(line):
                context_after.append(line)
            else:
                break

        jobs.append(
            {
                "context_before": context_before,
                "date_line": lines[date_idx],
                "date_match": date_match,
                "context_after": context_after,
                "linkedin_order": rank,  # 0 = first shown (most recent)
            }
        )

    return jobs


# ── Field Extraction from a Raw Job Dict ─────────────────────────────────────

def _extract_fields(
    raw: dict, profile_id: str, country: str, total_jobs: int
) -> dict:
    """
    Convert a raw job dict (from _segment_jobs) into a flat record with all
    extracted and derived fields.
    """
    # ── Title & Company ───────────────────────────────────────────────────────
    before = raw["context_before"]

    # Standard LinkedIn structure (most common):
    #   line[0] (further from date) = job title
    #   line[1] (closer to date)   = company [· employment type]
    #
    # Exception — company-group entries where the company name is the group
    # header above, and the title is indented just above the date:
    #   line[0] = "Company Name"         ← org header, no role keywords
    #   line[1] = "IT Analyst / Engineer" ← clear role title
    #
    # Heuristic: if line[0] has NO seniority/role keywords but line[-1] DOES,
    # treat line[-1] as the title and line[0] as the company (swap).

    _ROLE_PATTERN = re.compile(
        "|".join(SENIORITY_KEYWORDS.values()), re.IGNORECASE
    )

    title: str | None = None
    company_raw: str | None = None

    if len(before) == 0:
        pass  # both remain None
    elif len(before) == 1:
        title = before[0]
    else:
        first_has_role = bool(_ROLE_PATTERN.search(before[0]))
        last_has_role = bool(_ROLE_PATTERN.search(before[-1]))
        if not first_has_role and last_has_role:
            # Company-group layout: title is closest to date, company is the header
            title = before[-1]
            company_raw = before[0]
        else:
            # Standard layout: title first, company second
            title = before[0]
            company_raw = before[-1]

    # Strip employment type suffix from company line (e.g. "Oracle · Full-time" → "Oracle")
    company = None
    if company_raw:
        company = re.split(r"\s*·\s*", company_raw)[0].strip() or None

    # ── Dates ─────────────────────────────────────────────────────────────────
    dm = raw["date_match"]
    start_str = dm.group("start")
    end_str = dm.group("end")
    duration_str = dm.group("duration")

    start_year, start_month = _parse_year_month(start_str)
    is_current = (end_str.strip().lower() == "present")
    end_year, end_month = (None, None) if is_current else _parse_year_month(end_str)

    duration_months = _parse_duration_str(duration_str)

    # ── Work Mode ─────────────────────────────────────────────────────────────
    work_mode = None
    for line in raw["context_after"]:
        wm = WORK_MODE_RE.search(line)
        if wm:
            work_mode = wm.group(1)
            break

    # ── Derived Fields ────────────────────────────────────────────────────────
    # position_in_career: 1 = most recent (LinkedIn shows newest first)
    position_in_career = raw["linkedin_order"] + 1
    # Reverse so that 1 = earliest job (better for timeline models)
    position_from_start = total_jobs - raw["linkedin_order"]

    seniority_hint = _infer_seniority(title) if title else "unknown"

    return {
        "profile_id": profile_id,
        "country": country,
        "position_in_career": position_from_start,      # 1 = first/earliest job
        "position_from_recent": position_in_career,     # 1 = current/most recent
        "job_title": title,
        "company": company,
        "start_year": start_year,
        "start_month": start_month,
        "end_year": end_year,
        "end_month": end_month,
        "duration_months": duration_months,
        "is_current": is_current,
        "seniority_hint": seniority_hint,
        "raw_date_line": raw["date_line"],      # audit only — not used in analysis
    }


# ── Company carry-forward for group roles ────────────────────────────────────

def _carry_forward_company(records: list[dict]) -> list[dict]:
    """
    LinkedIn sometimes groups multiple roles under one company header.
    After de-duplication the company name appears on the first role of the
    group but is absent (None) on subsequent sibling roles.

    This pass fills those gaps: if a record has no company but the
    immediately preceding record (by position_from_recent) has one,
    AND both records share overlapping date ranges with the same employer
    context, carry the company name forward.

    Conservative rule: propagate only when:
      - current company is None
      - previous company is not None
      - gap between previous end_year and current start_year is <= 1 year
        (i.e. they belong to the same employer tenure)
    """
    if not records:
        return records

    # Work on a copy sorted by position_from_recent ascending (1 = most recent)
    result = list(records)  # already ordered by linkedin_order

    for i in range(1, len(result)):
        curr = result[i]
        prev = result[i - 1]

        if curr["company"] is not None:
            continue  # already has a company
        if prev["company"] is None:
            continue  # nothing to carry forward

        # Date-overlap / proximity check.
        # Two signals that two roles belong to the same company-group block:
        #   1. Same start year — identical date on both sibling roles
        #   2. Internal move — curr started later within an ongoing prev tenure
        #      AND curr has already ended (not a concurrent parallel job)
        curr_start = curr.get("start_year")
        prev_start = prev.get("start_year")
        prev_is_current = prev.get("is_current", False)
        curr_is_current = curr.get("is_current", False)

        same_start = (
            curr_start is not None
            and prev_start is not None
            and curr_start == prev_start
        )
        # Internal move: prev is ongoing, curr started later AND has ended.
        # The "has ended" guard prevents two concurrent self-employed / side
        # roles from being incorrectly merged under one company.
        internal_move = (
            prev_is_current
            and not curr_is_current          # curr has a definite end date
            and curr_start is not None
            and prev_start is not None
            and curr_start > prev_start
        )

        if same_start or internal_move:
            result[i] = {**curr, "company": prev["company"]}

    return result


# ── Public API ────────────────────────────────────────────────────────────────

def parse_experience_block(
    profile_id: str, country: str, experience_text: str
) -> list[dict]:
    """
    Parse a single profile's (pre-cleaned) experience block into job records.

    Args:
        profile_id:       Unique profile identifier.
        country:          Country label.
        experience_text:  Cleaned multiline LinkedIn experience string.
                          Should be passed through clean_experience_text() first.

    Returns:
        List of dicts, one per job detected in the block.
    """
    lines = _clean_lines(experience_text)
    raw_jobs = _segment_jobs(lines)
    total = len(raw_jobs)
    records = [
        _extract_fields(raw, profile_id, country, total)
        for raw in raw_jobs
    ]
    # Post-processing: fill missing company names for group roles
    records = _carry_forward_company(records)
    return records


def parse_profiles(raw_csv_path: str) -> pd.DataFrame:
    """
    Read the raw profiles CSV, pre-process each experience block, then parse.

    Pipeline:
      1. clean_experience_text()  — strip noise (logos, duplicates, etc.)
      2. parse_experience_block() — segment into jobs, extract fields
      3. _carry_forward_company() — fill group-role company gaps

    Args:
        raw_csv_path: Path to data/raw/raw_profiles.csv

    Returns:
        DataFrame with one row per job, all extracted fields as columns.
    """
    from src.preprocessing.clean_raw import clean_experience_text

    df_raw = pd.read_csv(raw_csv_path, dtype={"profile_id": str})

    all_records: list[dict] = []
    for _, row in df_raw.iterrows():
        cleaned_text = clean_experience_text(str(row["experience"]))
        records = parse_experience_block(
            profile_id=str(row["profile_id"]),
            country=row["country"],
            experience_text=cleaned_text,
        )
        all_records.extend(records)

    df_jobs = pd.DataFrame(all_records)

    # Enforce sensible dtypes
    int_cols = ["start_year", "start_month", "end_year", "end_month", "duration_months",
                "position_in_career", "position_from_recent"]
    for col in int_cols:
        df_jobs[col] = pd.to_numeric(df_jobs[col], errors="coerce").astype("Int64")

    return df_jobs
