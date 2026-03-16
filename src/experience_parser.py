"""
Run the full experience parsing pipeline.

Usage (from project root):
    python src/experience_parser.py

Reads   : data/raw/raw_profiles.csv
Writes  : data/processed/parsed_jobs.csv
"""

import sys
import os

# Allow running from project root without editable install
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.parsing.experience_parser import parse_profiles

RAW_PATH = "data/raw/raw_profiles.csv"
OUT_PATH = "data/processed/parsed_jobs.csv"


def main() -> None:
    print(f"Parsing experience data from: {RAW_PATH}")
    df_jobs = parse_profiles(RAW_PATH)

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df_jobs.to_csv(OUT_PATH, index=False)

    print(f"\nParsed {len(df_jobs)} job entries from {df_jobs['profile_id'].nunique()} profiles.")
    print(f"Saved to: {OUT_PATH}\n")

    # Quick inspection
    print("── Columns ────────────────────────────────────────")
    print(df_jobs.dtypes.to_string())
    print("\n── Sample output ──────────────────────────────────")
    display_cols = [
        "profile_id", "country", "position_in_career",
        "job_title", "company",
        "start_year", "end_year", "duration_months",
        "is_current", "seniority_hint",
    ]
    # Only include columns that exist in the dataframe
    display_cols = [col for col in display_cols if col in df_jobs.columns]
    print(df_jobs[display_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
