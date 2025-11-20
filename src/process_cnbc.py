import pandas as pd
import re

# ==========================================
# CONFIGURATION
# ==========================================
INPUT_FILE = "../data/cnbc_news_database.csv" 
OUTPUT_FILE = "../data/clean_news_2021.csv"

# Define the 2021 window
START_DATE = pd.to_datetime("2021-01-01").date()
END_DATE = pd.to_datetime("2021-12-31").date()

# ==========================================
# CLEANING FUNCTIONS
# ==========================================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ==========================================
# PROCESSING
# ==========================================
print(f"Loading {INPUT_FILE}...")
df = pd.read_csv(INPUT_FILE, on_bad_lines='skip')

# Parse Dates
# This forces all mixed timezones into UTC so pandas recognizes them as dates
print("Parsing dates...")
df['parsed_date'] = pd.to_datetime(df['published_at'], errors='coerce', utc=True).dt.date

# Filter for 2021
df_2021 = df[
    (df['parsed_date'] >= START_DATE) & 
    (df['parsed_date'] <= END_DATE)
].copy()

print(f"Filtered down to {len(df_2021)} articles from 2021.")

# Clean Titles
# Using 'title' based on the header you provided
print("Cleaning titles...")
df_2021['clean_headline'] = df_2021['title'].apply(clean_text)

# Generate IDs
# We create a simple 1, 2, 3... ID for the database
df_2021['article_id'] = range(1, len(df_2021) + 1)

# Format for MySQL
final_df = pd.DataFrame({
    'article_id': df_2021['article_id'],
    'date': df_2021['parsed_date'],
    'headline': df_2021['clean_headline'],
    'source': 'CNBC',
    'url': df_2021['url']
})

# Save
final_df.to_csv(OUTPUT_FILE, index=False)
print(f"Success! Saved to {OUTPUT_FILE}")
print(final_df.head())