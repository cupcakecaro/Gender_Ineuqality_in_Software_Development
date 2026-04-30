from __future__ import annotations

import contextlib
import io
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
from google import genai
from google.genai.errors import ClientError
from lifelines import CoxPHFitter


@dataclass
class Experience:
    """Represents a single work experience entry from a LinkedIn profile.

    Designed to map directly to a CSV row.
    """

    profile_id: int
    job_title: str
    country: Optional[str]
    start_date: Optional[str]  # e.g. "2020-01" or "Jan 2020"
    end_date: Optional[str]  # None means present/current role
    company: Optional[str] = None  # Optional field for company name
    position_in_career: Optional[int] = None  # Optional field for position in career timeline


class GeminiClient:
    """Thin wrapper around google-genai that exposes generate_text(prompt) -> str."""

    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self._client = genai.Client(api_key=api_key)

    def generate_text(self, prompt: str) -> str:
        response = self._client.models.generate_content(model=self.model_name, contents=prompt)
        return response.text


def parse_experience_with_llm(
    profile_id: int,
    country: str,
    experience_text: str,
    client: GeminiClient,
    parse_prompt: str,
    max_retries: int = 3,
    rate_limit_delay: float = 0.0,
) -> list[Experience]:
    """Send raw experience text to the LLM and parse the JSON response into Experience objects.

    position_in_career is assigned so that 1 = oldest job, N = most recent job.
    LinkedIn lists jobs most-recent-first, so the first item in the array gets the highest index.
    """

    if pd.isna(experience_text) or not str(experience_text).strip():
        return []

    prompt = parse_prompt.format(experience_text=experience_text)

    for attempt in range(max_retries):
        try:
            raw_text = client.generate_text(prompt).strip()
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            jobs = json.loads(raw_text)
            n = len(jobs)
            experiences: list[Experience] = []
            for idx, job in enumerate(jobs):
                experiences.append(
                    Experience(
                        profile_id=profile_id,
                        job_title=job.get("job_title", "Unknown"),
                        country=country,
                        start_date=job.get("start_date"),
                        end_date=job.get("end_date") if not job.get("is_current") else None,
                        company=job.get("company"),
                        position_in_career=n - idx,  # most recent (first in list) -> highest index
                    )
                )
            if rate_limit_delay:
                time.sleep(rate_limit_delay)
            return experiences

        except (json.JSONDecodeError, KeyError) as exc:
            print(f"  JSON parse error for profile {profile_id} (attempt {attempt + 1}): {exc}")
            if attempt < max_retries - 1:
                time.sleep(5)
        except ClientError as exc:
            if exc.code == 429:
                wait = 60
                print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1})...")
                time.sleep(wait)
            else:
                print(f"  API error for profile {profile_id}: {exc}")
                break
        except Exception as exc:
            print(f"  Unexpected error for profile {profile_id}: {exc}")
            break

    return [
        Experience(
            profile_id=profile_id,
            job_title="PARSE_ERROR",
            country=country,
            start_date=None,
            end_date=None,
            company=None,
            position_in_career=None,
        )
    ]


def classify_job(
    job_title: str,
    client: GeminiClient,
    classify_prompt: str,
    max_retries: int = 3,
    rate_limit_delay: float = 0.0,
    valid_categories: Optional[set[str]] = None,
) -> str:
    """Classify a single job title using GeminiClient."""

    if valid_categories is None:
        valid_categories = {
            "Traditional Software Development",
            "Low-Code/No-Code Development",
            "Other",
        }

    prompt = classify_prompt.format(job_title=job_title)

    for attempt in range(max_retries):
        try:
            label = client.generate_text(prompt).strip()
            if rate_limit_delay:
                time.sleep(rate_limit_delay)
            return label if label in valid_categories else "Other"

        except ClientError as exc:
            if exc.code == 429:
                wait = 60
                print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1})...")
                time.sleep(wait)
            else:
                print(f"  API error for '{job_title}': {exc}")
                break
        except Exception as exc:
            print(f"  Unexpected error for '{job_title}': {exc}")
            break

    return "ERROR"


def classify_seniority(
    job_title: str,
    client: GeminiClient,
    seniority_prompt: str,
    max_retries: int = 3,
    rate_limit_delay: float = 0.0,
    valid_seniority: Optional[set[str]] = None,
) -> int:
    """Classify seniority level (0-7) for a single job title using GeminiClient."""

    if valid_seniority is None:
        valid_seniority = {"0", "1", "2", "3", "4", "5", "6", "7"}

    prompt = seniority_prompt.format(job_title=job_title)

    for attempt in range(max_retries):
        try:
            result = client.generate_text(prompt).strip()
            if result in valid_seniority:
                if rate_limit_delay:
                    time.sleep(rate_limit_delay)
                return int(result)
            print(f"  Invalid response '{result}' for '{job_title}' (attempt {attempt + 1})")

        except ClientError as exc:
            if exc.code == 429:
                wait = 60
                print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1})...")
                time.sleep(wait)
            else:
                print(f"  API error for '{job_title}': {exc}")
                break
        except Exception as exc:
            print(f"  Unexpected error for '{job_title}': {exc}")
            break

    return -1


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse a date string in 'YYYY-MM' or 'YYYY' format to a datetime object."""

    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    s = str(date_str).strip()
    if len(s) == 7 and s[4] == "-":
        try:
            return datetime.strptime(s, "%Y-%m")
        except ValueError:
            return None
    if len(s) == 4 and s.isdigit():
        try:
            return datetime(int(s), 1, 1)
        except ValueError:
            return None
    return None


def calc_duration_months(start_str: Optional[str], end_str: Optional[str]) -> Optional[int]:
    """Calculate duration in months between two date strings.

    Uses today's date if end_str is null and returns None if start_str is null.
    """

    start = parse_date(start_str)
    if start is None:
        return None
    end = parse_date(end_str)
    if end is None:
        end = datetime.today()
    months = (end.year - start.year) * 12 + (end.month - start.month)
    return max(months, 0)


def classify_profile(group: pd.DataFrame, mixed_threshold: float = 0.4) -> str:
    """Classify a profile based on the job_label distribution of all its roles."""

    labels = group["job_label"].value_counts()
    lcnc_count = labels.get("Low-Code/No-Code Development", 0)
    trad_count = labels.get("Traditional Software Development", 0)

    if lcnc_count > 0 and trad_count > 0:
        ratio = min(lcnc_count, trad_count) / max(lcnc_count, trad_count)
        if ratio >= mixed_threshold:
            return "Mixed"
        return "LCNC" if lcnc_count > trad_count else "Traditional Software Development"
    if lcnc_count > 0:
        return "LCNC"
    if trad_count > 0:
        return "Traditional Software Development"
    return "Other"


def parse_profile_date(value: Optional[str]) -> pd.Timestamp:
    """Parse YYYY-MM or YYYY date strings to pandas Timestamp."""

    if pd.isna(value):
        return pd.NaT
    s = str(value).strip()
    if not s:
        return pd.NaT
    if len(s) == 7 and s[4] == "-":
        return pd.to_datetime(s, format="%Y-%m", errors="coerce")
    if len(s) == 4 and s.isdigit():
        return pd.to_datetime(f"{s}-01", format="%Y-%m", errors="coerce")
    return pd.to_datetime(s, errors="coerce")


def months_between(start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> float:
    """Return elapsed months between two timestamps."""

    if pd.isna(start_ts) or pd.isna(end_ts):
        return np.nan
    return max((end_ts.year - start_ts.year) * 12 + (end_ts.month - start_ts.month), 0)


def summarize_profile(group: pd.DataFrame) -> pd.Series:
    """Build profile-level outcomes and covariates for progression analysis."""

    group = group.sort_values(["start_dt", "position_in_career"]).copy()

    start_candidates = group["start_dt"].dropna()
    if start_candidates.empty:
        return pd.Series(
            {
                "country": group["country"].iloc[0],
                "profile_label": group["profile_label"].iloc[0],
                "career_start_dt": pd.NaT,
                "last_observed_dt": pd.NaT,
                "duration_observed_months": np.nan,
                "event_a": 0,
                "time_to_event_a_months": np.nan,
                "event_b": 0,
                "time_to_event_b_months": np.nan,
                "baseline_seniority": np.nan,
                "number_of_roles": len(group),
                "lcnc_share": np.nan,
                "profile_label_primary": "Excluded_Other_Mixed",
            }
        )

    career_start = start_candidates.min()
    last_observed = group["end_dt_filled"].max()

    hit_a = group[group["seniority_level"] >= 4]
    event_a = int(not hit_a.empty)
    event_a_dt = hit_a["start_dt"].min() if event_a else pd.NaT

    hit_b = group[group["seniority_level"] >= 5]
    event_b = int(not hit_b.empty)
    event_b_dt = hit_b["start_dt"].min() if event_b else pd.NaT

    time_a = (
        months_between(career_start, event_a_dt)
        if event_a
        else months_between(career_start, last_observed)
    )
    time_b = (
        months_between(career_start, event_b_dt)
        if event_b
        else months_between(career_start, last_observed)
    )

    baseline_row = group[group["start_dt"] == career_start]
    baseline_seniority = (
        baseline_row["seniority_level"].dropna().iloc[0] if not baseline_row.empty else np.nan
    )

    lcnc_count = (group["job_label"] == "Low-Code/No-Code Development").sum()
    trad_count = (group["job_label"] == "Traditional Software Development").sum()
    denom = lcnc_count + trad_count
    lcnc_share = lcnc_count / denom if denom > 0 else np.nan

    profile_label = group["profile_label"].iloc[0]
    if profile_label in {"LCNC", "Traditional Software Development"}:
        profile_label_primary = profile_label
    else:
        profile_label_primary = "Excluded_Other_Mixed"

    return pd.Series(
        {
            "country": group["country"].iloc[0],
            "profile_label": profile_label,
            "career_start_dt": career_start,
            "last_observed_dt": last_observed,
            "duration_observed_months": months_between(career_start, last_observed),
            "event_a": event_a,
            "time_to_event_a_months": time_a,
            "event_b": event_b,
            "time_to_event_b_months": time_b,
            "baseline_seniority": baseline_seniority,
            "number_of_roles": len(group),
            "lcnc_share": lcnc_share,
            "profile_label_primary": profile_label_primary,
        }
    )


def fit_cox_model(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
) -> tuple[CoxPHFitter, pd.DataFrame]:
    """Fit a Cox model and return the fitted model and input dataframe."""

    model_df = df[
        [
            duration_col,
            event_col,
            "is_lcnc",
            "is_romania",
            "lcnc_x_romania",
            "baseline_seniority",
            "number_of_roles",
            "career_start_year",
        ]
    ].dropna().copy()

    cph = CoxPHFitter()
    cph.fit(model_df, duration_col=duration_col, event_col=event_col)
    return cph, model_df


def interpretation_line(summary_df: pd.DataFrame, term: str, label: str) -> str:
    """Build a short interpretation line for a Cox model coefficient."""

    if term not in summary_df.index:
        return f"{label}: term '{term}' not estimated."
    hr = summary_df.loc[term, "exp(coef)"]
    lo = summary_df.loc[term, "exp(coef) lower 95%"]
    hi = summary_df.loc[term, "exp(coef) upper 95%"]
    direction = "faster" if hr > 1 else "slower"
    return f"{label}: HR={hr:.2f} (95% CI {lo:.2f}-{hi:.2f}) -> {direction} progression vs reference."


def ph_report(
    cph_model: CoxPHFitter,
    model_df: pd.DataFrame,
    label: str,
    p_value_threshold: float = 0.05,
) -> str:
    """Return a proportional hazards diagnostics report as a formatted string."""

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        cph_model.check_assumptions(
            model_df, p_value_threshold=p_value_threshold, show_plots=False
        )
    return f"=== {label} ===\n" + buf.getvalue().strip() + "\n"
