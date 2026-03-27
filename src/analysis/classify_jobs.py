"""
UNIFIED JOB CLASSIFIER

Classifies job titles from parsed_jobs.csv into:
  - Traditional Software Development
  - Low-Code/No-Code Development
  - Leadership/Management
  - Other

Supported providers (--provider):
  gemini  — Google Gemini API (free tier: 15 req/min, 1500 req/day)
  openai  — OpenAI Chat Completions API

Usage:
  uv run src/analysis/classify_jobs.py --provider gemini
  uv run src/analysis/classify_jobs.py --provider openai --model gpt-4o-mini

Environment variables (loaded from .env):
  GEMINI_API_KEY  — Google Gemini API key
  GOOGLE_API_KEY  — Alternative key name for Gemini
  OPENAI_API_KEY  — OpenAI API key

Author: Master's thesis on gender inequality in software development
Date: March 2026
"""
from __future__ import annotations

import argparse
import os
import time
from abc import ABC, abstractmethod

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_CATEGORIES = frozenset(
    {
        "Traditional Software Development",
        "Low-Code/No-Code Development",
        "Leadership/Management",
        "Other",
    }
)

PROMPT_TEMPLATE = """Classify the following job title into exactly one of these categories:
- Traditional Software Development
- Low-Code/No-Code Development
- Leadership/Management
- Other

Rules:
- Traditional Software Development: software engineers, developers, programmers, \
QA/test engineers, data engineers, DevOps, data scientists, ML engineers, etc.
- Low-Code/No-Code Development: roles primarily using platforms such as Salesforce, \
OutSystems, Power Platform, ServiceNow, Mendix, Appian, Webflow, Bubble, Zapier, etc.
- Leadership/Management: engineering managers, CTOs, VPs of Engineering, tech leads \
with explicit people management responsibilities, project/programme managers.
- Other: anything that does not fit the above (e.g. sales, HR, marketing, finance, \
student, intern without a technical role).

Job title: {job_title}

Respond with only the category name, nothing else."""

MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class JobClassifierProvider(ABC):
    """Abstract interface that every classification backend must implement."""

    @abstractmethod
    def setup(self) -> None:
        """Initialise the provider (e.g. authenticate, check connectivity)."""

    @abstractmethod
    def classify(self, job_title: str) -> str:
        """
        Classify a single job title.

        Returns one of the VALID_CATEGORIES or "Unknown" on failure.
        """


# ---------------------------------------------------------------------------
# Provider: Google Gemini
# ---------------------------------------------------------------------------


class GeminiProvider(JobClassifierProvider):
    """Classify job titles using the Google Gemini API (free tier supported)."""

    # Stay comfortably under the 15 req/min free-tier limit.
    _REQUESTS_PER_MINUTE = 13

    def __init__(self, model: str | None = None) -> None:
        self.model = model or "gemini-2.0-flash"
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._client = None
        self._delay = 60 / self._REQUESTS_PER_MINUTE

    def setup(self) -> None:
        if not self.api_key:
            raise SystemExit(
                "No Gemini API key found. Set GEMINI_API_KEY in your .env file.\n"
                "Get a free key at: https://aistudio.google.com/app/apikey"
            )

        try:
            from google import genai  # noqa: PLC0415
            from google.genai.errors import ClientError  # noqa: PLC0415
        except ImportError as exc:
            raise SystemExit(
                "The 'google-genai' package is not installed. Run: uv add google-genai"
            ) from exc

        self._genai = genai
        self._ClientError = ClientError
        self._client = genai.Client(api_key=self.api_key)
        print(f"Gemini provider ready — model: {self.model}")

    def classify(self, job_title: str) -> str:
        assert self._client is not None, "Call setup() before classify()."
        prompt = PROMPT_TEMPLATE.format(job_title=job_title)
        try:
            response = self._client.models.generate_content(
                model=self.model, contents=prompt
            )
            raw = response.text.strip()
            result = raw if raw in VALID_CATEGORIES else "Other"
        except self._ClientError as exc:
            # Surface rate-limit details; caller handles retry.
            raise exc

        time.sleep(self._delay)
        return result


# ---------------------------------------------------------------------------
# Provider: OpenAI
# ---------------------------------------------------------------------------


class OpenAIProvider(JobClassifierProvider):
    """Classify job titles using the OpenAI Chat Completions API."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or "gpt-4o-mini"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None

    def setup(self) -> None:
        if not self.api_key:
            raise SystemExit(
                "No OpenAI API key found. Set OPENAI_API_KEY in your .env file."
            )

        try:
            import openai  # noqa: PLC0415
        except ImportError as exc:
            raise SystemExit(
                "The 'openai' package is not installed. Run: uv add openai"
            ) from exc

        self._client = openai.OpenAI(api_key=self.api_key)
        print(f"OpenAI provider ready — model: {self.model}")

    def classify(self, job_title: str) -> str:
        assert self._client is not None, "Call setup() before classify()."
        prompt = PROMPT_TEMPLATE.format(job_title=job_title)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=32,
        )
        raw = response.choices[0].message.content.strip()
        return raw if raw in VALID_CATEGORIES else "Other"


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

_PROVIDERS: dict[str, type[JobClassifierProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
}


# ---------------------------------------------------------------------------
# Core classification loop
# ---------------------------------------------------------------------------


def _preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows without a usable job title."""
    return df[df["job_title"].notna() & (df["job_title"].str.strip() != "")].reset_index(
        drop=True
    )


def run_classification(
    provider: JobClassifierProvider,
    input_csv: str,
    output_csv: str,
) -> pd.DataFrame:
    """
    Load job titles from *input_csv*, classify each one with *provider*,
    write results to *output_csv*, and return the annotated DataFrame.
    """
    df = pd.read_csv(input_csv)
    df = _preprocess(df)
    total = len(df)
    print(f"Classifying {total} job titles ...")

    results: list[str] = []

    for idx, row in df.iterrows():
        job_title: str = row["job_title"]
        classification = "Unknown"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                classification = provider.classify(job_title)
                print(f"[{idx + 1}/{total}] '{job_title}' -> {classification}")
                break
            except Exception as exc:  # noqa: BLE001
                wait = 2 * attempt
                print(
                    f"  Attempt {attempt}/{MAX_RETRIES} failed for '{job_title}': {exc}"
                )
                if attempt < MAX_RETRIES:
                    print(f"  Retrying in {wait}s ...")
                    time.sleep(wait)

        if classification == "Unknown":
            print(f"  Could not classify: '{job_title}'")

        results.append(classification)

    df["classification"] = results
    os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"\nDone. Results saved to: {output_csv}")

    counts = df["classification"].value_counts()
    print("\nClassification summary:")
    for category, count in counts.items():
        print(f"  {category}: {count} ({count / total * 100:.1f}%)")

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point for the unified job classifier."""
    parser = argparse.ArgumentParser(
        description="Classify job titles using a selectable model provider.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run src/analysis/classify_jobs.py --provider gemini
  uv run src/analysis/classify_jobs.py --provider openai --model gpt-4o-mini
        """,
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=list(_PROVIDERS),
        help=f"Model provider to use. Choices: {', '.join(_PROVIDERS)}",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name override. Gemini default: gemini-2.0-flash. OpenAI default: gpt-4o-mini.",
    )
    parser.add_argument(
        "--input",
        default="data/processed/parsed_jobs.csv",
        help="Path to input CSV (default: data/processed/parsed_jobs.csv).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output CSV. Defaults to data/processed/classified_jobs_<provider>.csv.",
    )

    args = parser.parse_args()
    output_csv = args.output or f"data/processed/classified_jobs_{args.provider}.csv"

    provider = _PROVIDERS[args.provider](model=args.model)
    provider.setup()
    run_classification(provider, args.input, output_csv)


if __name__ == "__main__":
    main()
