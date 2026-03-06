"""
Script to clean raw_profiles.csv by:
- Merging fragmented rows into single profile rows
- Removing empty/irrelevant rows
- Standardizing columns: profile_id, country, experience
- Removing unnecessary blanks/semicolons

Output: Overwrites the original raw_profiles.csv with cleaned data
"""
import pandas as pd
import re

RAW_PATH = "data/raw/raw_profiles.csv"

# Read the file as raw lines
with open(RAW_PATH, encoding="utf-8") as f:
    lines = f.readlines()

cleaned_rows = []
current_profile = None

for line in lines:
    # Remove excessive semicolons and whitespace
    parts = [p.strip() for p in line.strip().split(';') if p.strip()]
    # Detect new profile by profile_id (should be int or id string at start)
    if parts and re.match(r'^\d+', parts[0]):
        # Save previous profile if exists
        if current_profile:
            cleaned_rows.append(current_profile)
        # Start new profile
        profile_id = parts[0]
        country = parts[1] if len(parts) > 1 else ''
        experience = ' '.join(parts[2:]) if len(parts) > 2 else ''
        current_profile = [profile_id, country, experience]
    elif current_profile and parts:
        # Continuation of experience for current profile
        current_profile[2] += ' ' + ' '.join(parts)
# Save last profile
if current_profile:
    cleaned_rows.append(current_profile)

# Remove excessive whitespace in experience
for row in cleaned_rows:
    row[2] = re.sub(r'\s+', ' ', row[2]).strip()

# Write cleaned data back to CSV
with open(RAW_PATH, 'w', encoding='utf-8') as f:
    f.write('profile_id;country;experience\n')
    for row in cleaned_rows:
        f.write(';'.join(row) + '\n')
