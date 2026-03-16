"""
GOOGLE GEMINI JOB CLASSIFIER (FREE TIER)

- Uses Google Gemini API with generous free tier
- Free limits: 15 requests/minute, 1500 requests/day
- For 300 jobs: ~20 minutes total, 100% FREE
- Get API key: https://aistudio.google.com/app/apikey

Setup:
1. Get free API key from: https://aistudio.google.com/app/apikey
2. Set environment variable in .env: GEMINI_API_KEY=your_key_here
3. Run: uv run src/analysis/classify_jobs_gemini.py

Author: Created for Master's thesis on gender inequality in software development
Date: March 2026
"""
import pandas as pd
import time
import os
import re
from google import genai
from google.genai.errors import ClientError
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATION ===
INPUT_CSV = "data/processed/parsed_jobs.csv"
OUTPUT_CSV = "data/processed/classified_jobs_gemini.csv"
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-2.0-flash"  # Available on free tier
REQUESTS_PER_MINUTE = 13  # Stay under 15/min limit with safety margin
MAX_RETRIES = 3

VALID_CATEGORIES = {
    "Traditional Software Development",
    "Low-Code/No-Code Development",
    "Leadership/Management",
    "Other"
}

PROMPT_TEMPLATE = """Classify the following job title into one of these categories:
- Traditional Software Development
- Low-Code/No-Code Development
- Leadership/Management
- Other

Job title: {job_title}

Respond with only the category name, nothing else."""

# === PREPROCESSING ===
def preprocess_data(df):
    """Filter out rows with missing or malformed job titles."""
    df = df[df['job_title'].notna() & (df['job_title'].str.strip() != "")]
    return df

# === MAIN FUNCTION ===
def classify_jobs():
    """Classify jobs using Google Gemini API with retry logic."""
    df = pd.read_csv(INPUT_CSV)
    df = preprocess_data(df)
    print(f"📋 Classifying {len(df)} job titles using {MODEL}...")

    client = genai.Client(api_key=API_KEY)
    delay = 60 / REQUESTS_PER_MINUTE

    results = []
    for index, row in df.iterrows():
        job_title = row['job_title']
        classification = 'Unknown'

        for attempt in range(MAX_RETRIES):
            try:
                prompt = PROMPT_TEMPLATE.format(job_title=job_title)
                response = client.models.generate_content(model=MODEL, contents=prompt)
                raw = response.text.strip()
                classification = raw if raw in VALID_CATEGORIES else 'Other'
                print(f"✅ [{index}] '{job_title}' → {classification}")
                break
            except ClientError as e:
                code = e.code if hasattr(e, 'code') else (e.args[0] if e.args else 0)
                if code == 429 or '429' in str(e):
                    match = re.search(r'retry in (\d+)', str(e))
                    wait = int(match.group(1)) + 5 if match else 60
                    print(f"⏳ Rate limited. Waiting {wait}s before retry {attempt+1}/{MAX_RETRIES}...")
                    time.sleep(wait)
                else:
                    print(f"⚠️ API error on row {index} ('{job_title}'): {e}")
                    break
            except Exception as e:
                print(f"⚠️ Unexpected error on row {index} ('{job_title}'): {e}")
                break

        if classification == 'Unknown':
            print(f"🔍 Could not classify: '{job_title}'")

        results.append(classification)
        time.sleep(delay)

    df['classification'] = results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Done. Results saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    classify_jobs()
