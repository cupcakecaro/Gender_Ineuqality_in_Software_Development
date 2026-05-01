"""
LLM-based job classification for LCNC vs. Traditional roles.

- Reads: data/processed/parsed_jobs.csv
- Classifies each job as 'LCNC', 'Traditional', or 'Unknown' using an LLM API
- Saves: data/processed/classified_jobs.csv

Instructions:
- Edit the PROMPT_TEMPLATE below to adjust classification rules or examples.
- Set your LLM API key and endpoint as needed.
- Run: python src/analysis/classify_jobs_llm.py
"""
import pandas as pd
import time
import os
from openai import OpenAI  # pip install openai

# === CONFIGURATION ===
INPUT_CSV = "data/processed/parsed_jobs.csv"
OUTPUT_CSV = "data/processed/classified_jobs.csv"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4"  # or "gpt-3.5-turbo"
TEMPERATURE = 0.2

# === PROMPT TEMPLATE ===
PROMPT_TEMPLATE = """
You are an expert in software job classification. 
Classify the following job as either "LCNC" (Low-Code/No-Code), "Traditional", or "Unknown" based on the job title and description.

Rules:
- "LCNC" if the job is primarily about building apps or automations with low-code/no-code platforms (e.g., PowerApps, Mendix, Webflow, Bubble, Zapier, OutSystems,Appian, Simplifier, Neptune Software, etc.).
- "Traditional" if the job requires writing custom code in languages like Python, Java, C#, JavaScript, etc.
- "Unknown" if you cannot tell from the information.

Example 1:
Job: Power Platform Developer at Contoso, building business apps with PowerApps and Automate.
Label: LCNC

Example 2:
Job: Senior Java Backend Engineer at Acme Corp, developing REST APIs.
Label: Traditional

Example 3:
Job: IT Consultant, responsible for various digital solutions.
Label: Unknown

Now classify this job:
Job: {job_text}
Label:
"""

# === END CONFIGURATION ===

def classify_job(job_text, api_key=API_KEY, model=MODEL, temperature=TEMPERATURE):
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
    
    client = OpenAI(api_key=api_key)
    prompt = PROMPT_TEMPLATE.format(job_text=job_text)
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=10,
        n=1,
        stop=["\n"]
    )
    label = response.choices[0].message.content.strip()
    return label

def main():
    df = pd.read_csv(INPUT_CSV)
    # Use job_title, company, and raw_date_line for context
    def make_job_text(row):
        parts = []
        if pd.notna(row.get('job_title')):
            parts.append(str(row['job_title']))
        if pd.notna(row.get('company')):
            parts.append(str(row['company']))
        if pd.notna(row.get('raw_date_line')):
            parts.append(str(row['raw_date_line']))
        return ' | '.join(parts)
    
    df['job_text'] = df.apply(make_job_text, axis=1)
    labels = []
    for i, row in df.iterrows():
        print(f"Classifying job {i+1}/{len(df)}...")
        try:
            label = classify_job(row['job_text'])
        except Exception as e:
            print(f"Error: {e}")
            label = "ERROR"
        labels.append(label)
        time.sleep(1.2)  # To avoid rate limits
    df['lcnc_label'] = labels
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✓ Saved classified jobs to {OUTPUT_CSV}")
    print(df['lcnc_label'].value_counts())

if __name__ == "__main__":
    main()
