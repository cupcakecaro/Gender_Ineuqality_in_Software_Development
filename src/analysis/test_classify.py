"""
TEST VERSION: Classify only 3 jobs to verify the script works before running on all data.
This will cost less than $0.01 to test.
"""
import pandas as pd
import os
from openai import OpenAI

# === CONFIGURATION ===
INPUT_CSV = "data/processed/parsed_jobs.csv"
TEST_OUTPUT_CSV = "data/processed/test_classified_jobs.csv"
API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"  # Cheaper model for testing
TEMPERATURE = 0.2
TEST_SIZE = 3  # Only classify first 3 jobs

# === PROMPT TEMPLATE ===
PROMPT_TEMPLATE = """
You are an expert in software job classification. 
Classify the following job as either "LCNC" (Low-Code/No-Code), "Traditional", or "Unknown" based on the job title and description.

Rules:
- "LCNC" if the job is primarily about building apps or automations with low-code/no-code platforms (e.g., PowerApps, Mendix, Webflow, Bubble, Zapier, OutSystems, Appian, Simplifier, Neptune Software, etc.).
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

def classify_job(job_text, api_key, model, temperature):
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
    print(f"Testing classification on first {TEST_SIZE} jobs...")
    print(f"Using model: {MODEL}")
    print(f"API Key found: {'Yes' if API_KEY else 'No'}\n")
    
    if not API_KEY:
        print("ERROR: Please set OPENAI_API_KEY environment variable first:")
        print("export OPENAI_API_KEY=sk-...")
        return
    
    df = pd.read_csv(INPUT_CSV)
    
    # Only take first TEST_SIZE jobs
    df_test = df.head(TEST_SIZE).copy()
    
    # Make job text from available fields
    def make_job_text(row):
        parts = []
        if pd.notna(row.get('job_title')):
            parts.append(str(row['job_title']))
        if pd.notna(row.get('company')):
            parts.append(str(row['company']))
        if pd.notna(row.get('raw_date_line')):
            parts.append(str(row['raw_date_line']))
        return ' | '.join(parts)
    
    df_test['job_text'] = df_test.apply(make_job_text, axis=1)
    
    labels = []
    for i, row in df_test.iterrows():
        print(f"Classifying job {i+1}/{len(df_test)}...")
        print(f"  Job text: {row['job_text'][:100]}...")
        try:
            label = classify_job(row['job_text'], API_KEY, MODEL, TEMPERATURE)
            print(f"  → Label: {label}\n")
        except Exception as e:
            print(f"  → Error: {e}\n")
            label = "ERROR"
        labels.append(label)
    
    df_test['lcnc_label'] = labels
    df_test.to_csv(TEST_OUTPUT_CSV, index=False)
    
    print(f"\n✓ Test complete! Results saved to {TEST_OUTPUT_CSV}")
    print(f"\nLabel counts:")
    print(df_test['lcnc_label'].value_counts())
    print(f"\nIf this looks good, run the full classification script:")
    print("python src/analysis/classify_jobs_llm.py")

if __name__ == "__main__":
    main()
