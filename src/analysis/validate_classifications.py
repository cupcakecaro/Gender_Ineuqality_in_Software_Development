"""
Validation Helper: Compare different classification methods

Run after you've created classified.csv files to compare results.
"""
import pandas as pd
import os

def load_if_exists(path):
    """Load CSV if it exists, return None otherwise."""
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def main():
    print("=" * 70)
    print("CLASSIFICATION VALIDATION HELPER")
    print("=" * 70)
    
    # Load all available classified datasets
    files = {
        'rules': 'data/processed/classified_jobs_rules.csv',
        'gemini': 'data/processed/classified_jobs_gemini.csv',
        'openai': 'data/processed/classified_jobs.csv',
    }
    
    datasets = {}
    for name, path in files.items():
        df = load_if_exists(path)
        if df is not None:
            datasets[name] = df
            print(f"\n✅ Found: {name} ({len(df)} jobs)")
            print(f"   Path: {path}")
            if 'lcnc_label' in df.columns:
                print(f"   Distribution: {dict(df['lcnc_label'].value_counts())}")
    
    if not datasets:
        print("\n❌ No classified datasets found yet.")
        print("   Run one of the classifiers first:")
        print("   - python src/analysis/classify_jobs_rules.py")
        print("   - python src/analysis/classify_jobs_gemini.py")
        print("   - python src/analysis/classify_jobs_llm.py")
        return
    
    # Compare if multiple methods available
    if len(datasets) > 1:
        print("\n" + "=" * 70)
        print("COMPARISON BETWEEN METHODS")
        print("=" * 70)
        
        methods = list(datasets.keys())
        df1_name, df2_name = methods[0], methods[1]
        df1, df2 = datasets[df1_name], datasets[df2_name]
        
        # Merge on profile_id and position
        merged = df1[['profile_id', 'position_in_career', 'job_title', 'lcnc_label']].merge(
            df2[['profile_id', 'position_in_career', 'lcnc_label']],
            on=['profile_id', 'position_in_career'],
            suffixes=(f'_{df1_name}', f'_{df2_name}')
        )
        
        # Calculate agreement
        label1 = f'lcnc_label_{df1_name}'
        label2 = f'lcnc_label_{df2_name}'
        
        agreement = (merged[label1] == merged[label2]).sum()
        agreement_pct = (agreement / len(merged)) * 100
        
        print(f"\n📊 Agreement between {df1_name} and {df2_name}:")
        print(f"   {agreement}/{len(merged)} jobs agree ({agreement_pct:.1f}%)")
        
        # Show disagreements
        disagreements = merged[merged[label1] != merged[label2]]
        if len(disagreements) > 0:
            print(f"\n⚠️  {len(disagreements)} disagreements found:")
            print("   First 10 examples:")
            print("-" * 70)
            for i, row in disagreements.head(10).iterrows():
                print(f"   {row['job_title'][:50]}")
                print(f"      {df1_name}: {row[label1]}")
                print(f"      {df2_name}: {row[label2]}")
                print()
    
    # Sample for manual validation
    print("\n" + "=" * 70)
    print("SAMPLE FOR MANUAL VALIDATION")
    print("=" * 70)
    print("\nRandom sample of 30 jobs for manual validation:")
    print("(Use these to calculate accuracy)")
    print("-" * 70)
    
    # Use first available dataset
    df = list(datasets.values())[0]
    sample = df.sample(n=min(30, len(df)), random_state=42)
    
    for i, (idx, row) in enumerate(sample.iterrows(), 1):
        print(f"\n{i}. {row.get('job_title', 'N/A')}")
        print(f"   Company: {row.get('company', 'N/A')}")
        print(f"   Country: {row.get('country', 'N/A')}")
        print(f"   Automated label: {row.get('lcnc_label', 'N/A')}")
        print(f"   Your label: ___________  (LCNC / Traditional / Unknown)")
    
    print("\n" + "=" * 70)
    print("After manual labeling, calculate accuracy:")
    print("  Accuracy = (correct labels) / 30")
    print("  Report this in your thesis methodology!")
    print("=" * 70)

if __name__ == "__main__":
    main()
