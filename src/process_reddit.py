import pandas as pd
import re
import datetime

# ==========================================
# CONFIGURATION
# ==========================================
FOLDER_PATH = "../data/reddit_wsb.csv"
OUTPUT_FILE = "../data/clean_reddit_2021.csv"
START_DATE = "2021-01-01"
END_DATE = "2021-12-31"

# Load the raw data
# Use 'on_bad_lines' to skip any malformed rows that might crash the script
df = pd.read_csv(FOLDER_PATH, on_bad_lines='skip')

# ==========================================
# CLEANING FUNCTIONS
# ==========================================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # Remove URLs (http://...)
    text = re.sub(r'http\S+', '', text)
    
    # Remove Reddit markdown links [text](link)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    
    # Remove newlines and tabs
    text = text.replace('\n', ' ').replace('\r', '').replace('\t', ' ')
    
    # Remove emojis and special symbols (keep alphanumeric and basic punctuation)
    text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"-]', '', text)
    
    return text.strip()

# ==========================================
# PROCESSING
# ==========================================

# Process the Date
# Convert the 'timestamp' column to a standard YYYY-MM-DD date
df['date'] = pd.to_datetime(df['timestamp']).dt.date

# Filter for 2021 window
start_date = pd.to_datetime(START_DATE).date()
end_date = pd.to_datetime(END_DATE).date()

df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

# Clean the Text Columns
print("Cleaning titles and bodies...")
df['title'] = df['title'].apply(clean_text)
df['body'] = df['body'].apply(clean_text)

# Remove rows where the title became empty (or was NaN)
# checks for empty strings "" or real NaNs
df = df[df['title'].str.strip().astype(bool)]

# Rename Columns to match MySQL Table
df = df.rename(columns={
    'id': 'post_id',
    'comms_num': 'comment_count'
})

# Handle Missing Data
df['body'] = df['body'].fillna("")

# Select ONLY the columns the database expects
final_columns = ['post_id', 'date', 'title', 'body', 'score', 'comment_count']
final_df = df[final_columns]

# Save to a new CSV
output_filename = OUTPUT_FILE
final_df.to_csv(output_filename, index=False)

print(f"Success! Saved {len(final_df)} rows to {output_filename}")
print(final_df.head())