"""
SIMPLE LLM JOB CLASSIFIER - Direct API Approach (No Complex Packages!)

Uses direct HTTP requests to Google Gemini API - avoids all package installation issues.
Only requires: requests, pandas (both already installed in your environment)

FREE TIER:
- 15 requests/minute, 1500 requests/day
- For 300 jobs: ~20 minutes, 100% FREE

Setup:
1. Get API key: https://aistudio.google.com/app/apikey
2. Set: export GEMINI_API_KEY=your_key_here
3. Run: python src/analysis/classify_jobs_llm_simple.py

Author: Master's thesis on gender inequality in software development
Date: March 2026
"""

import pandas as pd
import requests
import time
import os
import json

# === CONFIGURATION ===
INPUT_CSV = "data/processed/parsed_jobs.csv"
OUTPUT_CSV = "data/processed/classified_jobs_llm.csv"
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
REQUESTS_PER_MINUTE = 13  # Stay safely under 15/min limit
TEMPERATURE = 0.2

# === CLASSIFICATION PROMPT ===
PROMPT_TEMPLATE = """You are an expert in software job classification. 
Classify the following job as either "LCNC" (Low-Code/No-Code), "Traditional", or "Unknown".

Rules:
- "LCNC" if the job primarily involves building apps/automations with low-code/no-code platforms like:
  * PowerApps, Power Platform, Power Automate
  * Mendix, OutSystems, Appian
  * Webflow, Bubble, Retool
  * Zapier, Make (Integromat)
  * ServiceNow, Salesforce Lightning
  * SAP Build, Oracle APEX
  * Neptune Software, Simplifier
  
- "Traditional" if the job requires writing custom code in languages like:
  * Python, Java, C++, C#, JavaScript, TypeScript
  * Go, Rust, Ruby, PHP, Swift, Kotlin
  * SQL, React, Angular, Vue, Node.js
  * Software Engineer, Developer, Programmer roles
  
- "Unknown" if you cannot determine from the information provided

Example 1:
Job: Power Platform Developer at Microsoft
Label: LCNC

Example 2:
Job: Senior Java Backend Engineer at Tech Corp
Label: Traditional

Example 3:
Job: IT Consultant at Digital Solutions
Label: Unknown

Now classify this job:
Job: {job_text}

Respond with ONLY ONE WORD: LCNC, Traditional, or Unknown
Label:"""


def classify_job_http(job_text, api_key):
    """Classify a job using direct HTTP request to Gemini API."""
    
    # Skip if job_text is just "Unknown" or empty
    if not job_text or job_text.strip() == "Unknown":
        return "Unknown"
    
    prompt = PROMPT_TEMPLATE.format(job_text=job_text)
    
    # Build request payload
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": TEMPERATURE,
            "maxOutputTokens": 10,
            "topP": 0.95,
        }
    }
    
    # Make API request
    url = f"{API_URL}?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code != 200:
        error_detail = response.json().get('error', {}).get('message', 'Unknown error')
        raise Exception(f"{response.status_code} {error_detail}")
    
    # Extract label from response
    result = response.json()
    
    # Check if response was blocked or filtered
    candidates = result.get('candidates', [])
    if not candidates:
        raise Exception("No candidates - response may be blocked")
    
    candidate = candidates[0]
    
    # Check for content blocking
    finish_reason = candidate.get('finishReason', '')
    if finish_reason in ['SAFETY', 'RECITATION', 'OTHER']:
        raise Exception(f"Response blocked: {finish_reason}")
    
    # Extract text
    content = candidate.get('content', {})
    if not content or 'parts' not in content:
        # API returned empty response (happens with "Unknown" or very short inputs)
        return "Unknown"
    
    parts = content.get('parts', [])
    if not parts:
        # No parts in response
        return "Unknown"
    
    text = parts[0].get('text', '').strip()
    if not text:
        return "Unknown"
    
    # Get first word only
    label = text.split()[0] if text else "Unknown"
    return label


def main():
    print("\n" + "=" * 70)
    print("🤖 SIMPLE LLM JOB CLASSIFIER (Direct API - No Package Issues!)")
    print("=" * 70)
    
    # Check API key
    if not API_KEY:
        print("\n❌ ERROR: GEMINI_API_KEY environment variable not set")
        print("\n📝 GET YOUR FREE API KEY:")
        print("   1. Open: https://aistudio.google.com/app/apikey")
        print("   2. Sign in with Google")
        print("   3. Click 'Create API Key'")
        print("   4. Copy the key")
        print("\n🔑 SET THE API KEY:")
        print("   export GEMINI_API_KEY=your_key_here")
        print("\n💰 FREE TIER: 15 req/min, 1500 req/day - 100% FREE for research")
        print("=" * 70)
        return
    
    # Check input file
    if not os.path.exists(INPUT_CSV):
        print(f"\n❌ ERROR: Input file not found: {INPUT_CSV}")
        return
    
    # Load data
    df = pd.read_csv(INPUT_CSV)
    print(f"\n📊 Loaded {len(df)} jobs from {INPUT_CSV}")
    print(f"🤖 Using: Google Gemini 2.5 Flash (via direct HTTP)")
    print(f"⏱️  Rate limit: {REQUESTS_PER_MINUTE} requests/minute")
    
    # Estimate time
    total_minutes = len(df) / REQUESTS_PER_MINUTE
    print(f"⏱️  Estimated time: ~{int(total_minutes)} minutes for {len(df)} jobs")
    print(f"💰 Cost: $0.00 (free tier)")
    
    # Create job text
    def make_job_text(row):
        parts = []
        if pd.notna(row.get('job_title')):
            parts.append(str(row['job_title']))
        if pd.notna(row.get('company')):
            parts.append(str(row['company']))
        return ' at '.join(parts) if len(parts) == 2 else parts[0] if parts else 'Unknown'
    
    df['job_text'] = df.apply(make_job_text, axis=1)
    
    # Ask for confirmation
    print("\n" + "=" * 70)
    user_input = input("▶️  Ready to start classification? (yes/no): ").strip().lower()
    if user_input not in ['yes', 'y']:
        print("❌ Cancelled by user")
        return
    
    # Classify each job
    print("\n🔍 CLASSIFICATION IN PROGRESS...")
    print("=" * 70)
    
    labels = []
    errors = 0
    start_time = time.time()
    
    for i, row in df.iterrows():
        job_preview = row['job_text'][:55] + "..." if len(row['job_text']) > 55 else row['job_text']
        print(f"[{i+1:3d}/{len(df)}] {job_preview:60s} ", end="", flush=True)
        
        try:
            label = classify_job_http(row['job_text'], API_KEY)
            
            # Validate label
            label_clean = label.strip().upper()
            if 'LCNC' in label_clean:
                label = 'LCNC'
            elif 'TRADITIONAL' in label_clean:
                label = 'Traditional'
            elif 'UNKNOWN' in label_clean:
                label = 'Unknown'
            else:
                # LLM returned something unexpected
                label = 'Unknown'
            
            print(f"→ {label}")
            
        except Exception as e:
            error_msg = str(e)[:50]
            print(f"→ ERROR: {error_msg}")
            label = "Unknown"
            errors += 1
        
        labels.append(label)
        
        # Rate limiting
        wait_time = 60.0 / REQUESTS_PER_MINUTE
        time.sleep(wait_time)
    
    # Add labels to dataframe
    df['lcnc_label'] = labels
    elapsed_time = time.time() - start_time
    
    # Save results
    df.to_csv(OUTPUT_CSV, index=False)
    
    # Show statistics
    print("\n" + "=" * 70)
    print("📈 CLASSIFICATION RESULTS")
    print("=" * 70)
    
    counts = df['lcnc_label'].value_counts()
    for label, count in counts.items():
        percentage = (count / len(df)) * 100
        bar = "█" * int(percentage / 2)
        print(f"{label:12s}: {count:3d} jobs ({percentage:5.1f}%) {bar}")
    
    if errors > 0:
        print(f"\n⚠️  {errors} errors occurred (marked as Unknown)")
    
    # Show sample results
    print("\n📋 SAMPLE CLASSIFICATIONS:")
    print("-" * 70)
    for label in ['LCNC', 'Traditional', 'Unknown']:
        sample = df[df['lcnc_label'] == label].head(3)
        if len(sample) > 0:
            print(f"\n{label}:")
            for _, row in sample.iterrows():
                job_preview = row['job_text'][:65] + "..." if len(row['job_text']) > 65 else row['job_text']
                print(f"  • {job_preview}")
    
    print("\n" + "=" * 70)
    print("✅ CLASSIFICATION COMPLETE!")
    print("=" * 70)
    print(f"📁 Output saved to: {OUTPUT_CSV}")
    print(f"⏱️  Time taken: {int(elapsed_time/60)} min {int(elapsed_time%60)} sec")
    print(f"💰 Total cost: $0.00 (free tier)")
    print(f"\n🔬 Next steps:")
    print(f"   1. Review sample results above")
    print(f"   2. Manually validate ~30 random samples for accuracy")
    print(f"   3. Use classified data for career trajectory analysis")
    print("=" * 70)


if __name__ == "__main__":
    main()
