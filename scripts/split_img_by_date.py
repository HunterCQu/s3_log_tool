import pandas as pd
from datetime import datetime

# Read the CSV file
input_csv = "input.csv"  # Change to your actual file path
output_csv = "filtered_output.csv"

def extract_date_from_path(path):
    try:
        parts = path.split('/')
        date_str = parts[6]  # Extract the date part from the path
        return datetime.strptime(date_str, "%Y%m%d")
    except (IndexError, ValueError):
        return None

# Load CSV
df = pd.read_csv(input_csv)

# Convert date in the path to datetime format
df["Date"] = df["Image Path"].apply(extract_date_from_path)

# Filter rows where date is after 2024-11-01
cutoff_date = datetime(2024, 11, 1)
df_filtered = df[df["Date"] > cutoff_date]

# Drop the temporary Date column
df_filtered = df_filtered.drop(columns=["Date"])

# Save to new CSV file
df_filtered.to_csv(output_csv, index=False)

print(f"Filtered CSV saved to {output_csv}")
