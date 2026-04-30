"""
Legacy text pre-processing for raw LinkedIn experience blocks.

Not used by the main workflow. The canonical entry point is notebooks/pipeline.ipynb.

clean_raw.py
------------
Pre-processing step applied to raw LinkedIn experience text BEFORE parsing.
Handles format-level noise that is independent of job structure:

  1. De-duplicate concatenated lines  e.g. "Oracle · Full-timeOracle · Full-time"
  2. Remove consecutive duplicate lines  (LinkedIn renders title twice)
  3. Strip image alt-text artefacts      e.g. "SU Heroes - Hackathon Team logo"
  4. Remove duplicate experience blocks  (same company-group copy-pasted twice)
  5. Drop lines that are pure duration strings with no date anchor
     e.g. "2 yrs 4 mos2 yrs 4 mos"  (SENAI group header without dates)

Usage:
    from src.legacy.preprocessing.clean_raw import clean_experience_text, clean_profiles_df

    # Single text block
    cleaned = clean_experience_text(raw_text)

    # Full DataFrame
    df_clean = clean_profiles_df(df_raw)
"""

import re
import pandas as pd

# ── Patterns ──────────────────────────────────────────────────────────────────

# Lines that end with " logo" (LinkedIn image alt-text artefact)
LOGO_LINE_RE = re.compile(r"^.+\s+logo\s*$", re.IGNORECASE)

# Lines that are ONLY a duration string, no real date range
# e.g. "2 yrs 4 mos" or "2 yrs 4 mos2 yrs 4 mos"
DURATION_ONLY_RE = re.compile(
    r"^\d+\s*yr[s]?(\s+\d+\s*mo[s]?)?\s*(\d+\s*yr[s]?(\s+\d+\s*mo[s]?)?)?$",
    re.IGNORECASE,
)

# Lines that are only a bare employment type with nothing else
# e.g. "Full-time", "Part-time", "Full-timeFull-time" (before dedup)
EMPLOYMENT_TYPE_ONLY_RE = re.compile(
    r"^(Full-time|Part-time|Self-Employed|Contract|Freelance)$",
    re.IGNORECASE,
)

# A "company-group header block": company name + duration line (no real date range)
# Used to detect and collapse duplicate group blocks
# Signature: two consecutive non-empty non-date lines followed by a duration-only line
MONTH_ABBR = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
DATE_RANGE_RE = re.compile(
    r"(?:" + MONTH_ABBR + r"\s+\d{4}|\d{4})"
    r"\s*(?:-|to)\s*"
    r"(?:Present|" + MONTH_ABBR + r"\s+\d{4}|\d{4})",
    re.IGNORECASE,
)


# ── Core helpers ──────────────────────────────────────────────────────────────

def _deduplicate_concat(line: str) -> str:
    """
    Remove exact within-line duplication produced by LinkedIn copy-paste.
    e.g. 'Oracle · Full-timeOracle · Full-time' → 'Oracle · Full-time'
    Only acts on even-length strings where both halves are identical.
    """
    s = line.strip()
    n = len(s)
    if n >= 4 and n % 2 == 0:
        half = n // 2
        if s[:half] == s[half:]:
            return s[:half].strip()
    return s


def _block_signature(lines: list[str]) -> str:
    """
    Create a normalised fingerprint for a block of lines.
    Used to detect duplicate company-group blocks.
    Strips whitespace and lowercases everything.
    """
    return "\n".join(l.strip().lower() for l in lines if l.strip())


def _split_into_blocks(lines: list[str]) -> list[list[str]]:
    """
    Split a line list into blocks separated by blank lines.
    Each block is a list of non-empty lines.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(line)
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


# ── Main cleaning function ────────────────────────────────────────────────────

def clean_experience_text(text: str) -> str:
    """
    Apply all pre-processing cleaning steps to a single raw experience block.

    Steps (in order):
      1. Deduplicate concatenated within-line repetitions
      2. Remove "… logo" artefact lines
      3. Remove pure duration-only lines (no real date anchor)
      4. Remove consecutive duplicate lines
      5. Remove duplicate blank-line-separated blocks (same company copied twice)

    Args:
        text: Raw multiline LinkedIn experience string from raw_profiles.csv

    Returns:
        Cleaned string, ready for the parser.
    """
    # ── Step 1 & 2 & 3: per-line cleaning ────────────────────────────────────
    raw_lines = text.split("\n")
    step1: list[str] = []
    for raw in raw_lines:
        line = _deduplicate_concat(raw)
        # Drop "… logo" artefact lines
        if LOGO_LINE_RE.match(line.strip()):
            continue
        # Drop pure duration-only lines (group headers without real dates)
        if DURATION_ONLY_RE.match(line.strip()):
            continue
        # Drop bare employment-type-only lines (e.g. "Full-time" as standalone)
        if EMPLOYMENT_TYPE_ONLY_RE.match(line.strip()):
            continue
        step1.append(line)

    # ── Step 4: remove consecutive duplicate lines ───────────────────────────
    step2: list[str] = []
    for line in step1:
        if step2 and step2[-1].strip() == line.strip() and line.strip():
            continue
        step2.append(line)

    # ── Step 5: remove duplicate blocks ──────────────────────────────────────
    # Split into blank-line-separated blocks, deduplicate by fingerprint,
    # then reassemble preserving original blank-line spacing.
    blocks = _split_into_blocks(step2)
    seen_signatures: set[str] = set()
    unique_blocks: list[list[str]] = []
    for block in blocks:
        sig = _block_signature(block)
        if sig not in seen_signatures:
            seen_signatures.add(sig)
            unique_blocks.append(block)

    # Reassemble with blank line separators
    cleaned = "\n\n".join("\n".join(block) for block in unique_blocks)
    return cleaned


def clean_profiles_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply clean_experience_text to every row of the raw profiles DataFrame.

    Args:
        df: DataFrame with at minimum columns [profile_id, country, experience]

    Returns:
        Copy of df with the 'experience' column replaced by cleaned text.
    """
    df = df.copy()
    df["experience"] = df["experience"].astype(str).apply(clean_experience_text)
    return df
