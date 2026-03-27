import pandas as pd

file_path = "data/external/Gender_Equality_Index_Data.csv"
df = pd.read_csv(file_path)

# 1️⃣ Keep only overall index
df = df[df["(Sub-) Domain Scores"] == "Overall Gender Equality Index"]

# 2️⃣ Keep latest year
latest_year = df["Time"].max()
df = df[df["Time"] == latest_year]

# 3️⃣ Rename columns
df = df.rename(columns={
    "Geographic region": "Country",
    "Value": "GenderEqualityIndex"
})

# 4️⃣ Keep only needed columns
df = df[["Country", "GenderEqualityIndex"]]

# 5️⃣ Sort descending
df = df.sort_values(by="GenderEqualityIndex", ascending=False)

print(df)
df.to_csv("data/processed/country_index_clean.csv", index=False)