import pandas as pd

df = pd.read_csv("data/raw/raw_profiles.csv")

print("Column names:")
print(df.columns)

print("\nFirst rows:")
print(df.head())