"""
OLLAMA LOCAL JOB CLASSIFIER

- Uses a locally running Ollama instance (http://localhost:11434)
- No API key required — runs fully offline
- Model is configurable via OLLAMA_MODEL env var or --model CLI argument
- To list available models: `ollama list`
- To pull a model: `ollama pull <model_name>`

Setup:
1. Install Ollama: https://ollama.com/download
2. Start the Ollama server: `ollama serve`
3. Pull the default model: `ollama pull qwen3.5` (or any other model)
4. Optionally override the model:
   - via env var in .env: OLLAMA_MODEL=llama3.2
   - or via CLI: uv run src/analysis/classify_jobs_ollama.py --model llama3.2
5. Run: uv run src/analysis/classify_jobs_ollama.py

Author: Created for Master's thesis on gender inequality in software development
Date: March 2026
"""
import argparse
import os
import time

import ollama
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# === CLI ARGUMENTS ===
parser = argparse.ArgumentParser(description="Classify job titles using a local Ollama model.")
parser.add_argument(
    "--model",
    type=str,
    default=None,
    help="Name of the Ollama model to use (default: qwen3.5). "
         "Overrides OLLAMA_MODEL env var.",
)
parser.add_argument(
    "--input",
    type=str,
    default="data/processed/parsed_jobs.csv",
    help="Path to input CSV with job titles (default: data/processed/parsed_jobs.csv).",
)
parser.add_argument(
    "--output",
    type=str,
    default="data/processed/classified_jobs_ollama.csv",
    help="Path to output CSV (default: data/processed/classified_jobs_ollama.csv).",
)
parser.add_argument(
    "--host",
    type=str,
    default=None,
    help="Ollama host URL (default: http://localhost:11434 or OLLAMA_HOST env var).",
)
args = parser.parse_args()

# === CONFIGURATION ===
INPUT_CSV = args.input
OUTPUT_CSV = args.output
HOST = args.host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = args.model or os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
MAX_RETRIES = 3

VALID_CATEGORIES = {
    "Traditional Software Development",
    "Low-Code/No-Code Development",
    "Other",
}

PROMPT_TEMPLATE = """Classify the following job title into exactly one of these categories:
- Traditional Software Development
- Low-Code/No-Code Development
- Other

Rules:
- Traditional Software Development: software engineers, developers, programmers, QA/test engineers, data engineers, DevOps, etc.
- Low-Code/No-Code Development: roles primarily involving platforms like Salesforce, OutSystems, Power Platform, ServiceNow, Mendix, Appian, etc.
- Other: anything that does not fit the above (e.g. sales, HR, marketing, finance, student).

Job title: {job_title}

Respond with only the category name, nothing else."""


# === PREPROCESSING ===
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out rows with missing or empty job titles."""
    df = df[df["job_title"].notna() & (df["job_title"].str.strip() != "")]
    return df.reset_index(drop=True)


# === CLASSIFICATION ===
def classify_single(client: ollama.Client, job_title: str) -> str:
    """Send one job title to Ollama and return the category."""
    prompt = PROMPT_TEMPLATE.format(job_title=job_title)
    response = client.generate(model=MODEL, prompt=prompt)
    raw = response.response.strip()
    return raw if raw in VALID_CATEGORIES else "Other"


# === MAIN ===
def classify_jobs() -> None:
    """Classify all job titles in the input CSV using the configured Ollama model."""
    df = pd.read_csv(INPUT_CSV)
    df = preprocess_data(df)
    print(f"Classifying {len(df)} job titles using Ollama model '{MODEL}' at {HOST} ...")

    client = ollama.Client(host=HOST)

    # Verify model is available before starting
    try:
        available = [m.model for m in client.list().models]
        if MODEL not in available:
            print(
                f"Warning: model '{MODEL}' not found in Ollama. Available models: {available}\n"
                "Pull it with: ollama pull " + MODEL
            )
    except Exception as e:
        print(f"Warning: could not reach Ollama at {HOST}: {e}")
        print("Make sure Ollama is running (`ollama serve`) before proceeding.")
        raise SystemExit(1)

    results = []
    for idx, row in df.iterrows():
        job_title = row["job_title"]
        classification = "Unknown"

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                classification = classify_single(client, job_title)
                print(f"[{idx + 1}/{len(df)}] '{job_title}' -> {classification}")
                break
            except Exception as e:
                print(f"  Error on attempt {attempt}/{MAX_RETRIES} for '{job_title}': {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(2 * attempt)

        if classification == "Unknown":
            print(f"  Could not classify: '{job_title}'")

        results.append(classification)

    df["classification"] = results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nDone. Results saved to: {OUTPUT_CSV}")

    # Summary
    counts = df["classification"].value_counts()
    print("\nClassification summary:")
    for cat, count in counts.items():
        print(f"  {cat}: {count} ({count / len(df) * 100:.1f}%)")


if __name__ == "__main__":
    classify_jobs()
