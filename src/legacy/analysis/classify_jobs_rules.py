"""
OPTION A: RULE-BASED CLASSIFIER (100% FREE, No API needed)

- Uses keyword matching to classify jobs
- Completely free, works offline
- Good accuracy for clear cases
- Run: python src/analysis/classify_jobs_rules.py
"""
import pandas as pd
import re

# === CONFIGURATION ===
INPUT_CSV = "data/processed/parsed_jobs.csv"
OUTPUT_CSV = "data/processed/classified_jobs_rules.csv"

# === CLASSIFICATION RULES ===

# Low-code / No-code platforms and keywords
LCNC_KEYWORDS = [
    # Major platforms
    'powerapps', 'power apps', 'power platform', 'power automate',
    'mendix', 'outsystems', 'appian', 'simplifier',
    'bubble', 'webflow', 'zapier', 'airtable',
    'salesforce', 'servicenow', 'sharepoint developer',
    'neptune software', 'sap fiori', 'sap ui5',
    'low-code', 'low code', 'no-code', 'no code', 'lcnc',
    'citizen developer', 'power user',
    
    # Related terms
    'visual development', 'drag and drop', 'workflow automation',
    'process automation', 'rpa developer', 'uipath', 'automation anywhere',
]

# Traditional coding keywords
TRADITIONAL_KEYWORDS = [
    # Programming languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php',
    'kotlin', 'swift', 'go', 'rust', 'scala', 'perl',
    
    # Development roles
    'software engineer', 'software developer', 'backend developer', 'frontend developer',
    'full stack', 'fullstack', 'devops', 'data engineer',
    'machine learning', 'data scientist', 'ai engineer',
    
    # Technologies
    'react', 'angular', 'vue', 'node.js', 'django', 'flask',
    'spring', 'kubernetes', 'docker', 'aws', 'azure developer',
    'rest api', 'microservices', 'database developer', 'sql developer',
    'git', 'ci/cd', 'agile developer',
]

# Ambiguous titles (need more context)
AMBIGUOUS_KEYWORDS = [
    'consultant', 'analyst', 'architect', 'manager', 'lead',
    'specialist', 'administrator', 'support', 'technician',
]


def classify_job_by_rules(job_text):
    """
    Classify a job based on keyword matching.
    
    Returns:
        - 'LCNC' if LCNC keywords found
        - 'Traditional' if traditional dev keywords found
        - 'Unknown' if ambiguous or no clear match
    """
    if pd.isna(job_text):
        return 'Unknown'
    
    text_lower = str(job_text).lower()
    
    # Count keyword matches
    lcnc_matches = sum(1 for kw in LCNC_KEYWORDS if kw in text_lower)
    trad_matches = sum(1 for kw in TRADITIONAL_KEYWORDS if kw in text_lower)
    
    # Decision logic
    if lcnc_matches > 0 and lcnc_matches > trad_matches:
        return 'LCNC'
    elif trad_matches > 0 and trad_matches > lcnc_matches:
        return 'Traditional'
    elif lcnc_matches > 0 and trad_matches > 0:
        # Mixed signals - Unknown
        return 'Unknown'
    else:
        # Check if ambiguous title
        has_ambiguous = any(kw in text_lower for kw in AMBIGUOUS_KEYWORDS)
        if has_ambiguous:
            return 'Unknown'
        else:
            # No keywords found
            return 'Unknown'


def main():
    print("🔄 Starting RULE-BASED classification (100% FREE)...")
    print("=" * 60)
    
    df = pd.read_csv(INPUT_CSV)
    print(f"📊 Loaded {len(df)} jobs from {INPUT_CSV}")
    
    # Create job text from available fields
    def make_job_text(row):
        parts = []
        if pd.notna(row.get('job_title')):
            parts.append(str(row['job_title']))
        if pd.notna(row.get('company')):
            parts.append(str(row['company']))
        return ' | '.join(parts)
    
    df['job_text'] = df.apply(make_job_text, axis=1)
    
    # Classify each job
    print("\n🔍 Classifying jobs...")
    df['lcnc_label'] = df['job_text'].apply(classify_job_by_rules)
    
    # Save results
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved classified jobs to {OUTPUT_CSV}")
    
    # Show statistics
    print("\n📈 CLASSIFICATION RESULTS:")
    print("=" * 60)
    counts = df['lcnc_label'].value_counts()
    for label, count in counts.items():
        percentage = (count / len(df)) * 100
        print(f"  {label:12s}: {count:3d} jobs ({percentage:5.1f}%)")
    
    print("\n🔍 Sample classifications:")
    print("-" * 60)
    for label in ['LCNC', 'Traditional', 'Unknown']:
        sample = df[df['lcnc_label'] == label].head(2)
        if len(sample) > 0:
            print(f"\n{label}:")
            for _, row in sample.iterrows():
                job_preview = row['job_text'][:70] + "..." if len(row['job_text']) > 70 else row['job_text']
                print(f"  • {job_preview}")
    
    print("\n" + "=" * 60)
    print("✅ DONE! No API costs, works offline.")


if __name__ == "__main__":
    main()
