import pandas as pd
import yfinance as yf
import glob
import os

# ==========================================
# CONFIGURATION
# ==========================================
FOLDER_PATH = "../data/stock_market_data"  # Folder with Kaggle CSVs
OUTPUT_FILE = "../data/clean_stock_prices_2021.csv"
MEME_TICKERS = ['GME', 'AMC']
START_DATE = "2021-01-01"
END_DATE = "2021-12-31"

# The exact columns for the final database
EXPECTED_COLS = ['ticker', 'date', 'open_price', 'close_price', 'high_price', 'low_price', 'volume']

data_frames = []

# ==========================================
# READ KAGGLE FILES
# ==========================================
print("--- Processing Kaggle CSVs ---")
csv_files = glob.glob(os.path.join(FOLDER_PATH, "*.csv"))

for filename in csv_files:
    try:
        # Read CSV
        df = pd.read_csv(filename)
        
        # Get Ticker from filename
        ticker = os.path.splitext(os.path.basename(filename))[0]
        df['ticker'] = ticker
        
        # Rename columns to standard
        # Handle cases where 'Adj Close' exists or doesn't
        if 'Close' in df.columns:
            df = df.rename(columns={'Close': 'close_price'})
        elif 'Adj Close' in df.columns:
            df = df.rename(columns={'Adj Close': 'close_price'})
            
        df = df.rename(columns={
            'Date': 'date', 
            'Open': 'open_price', 
            'High': 'high_price', # NEW
            'Low': 'low_price',   # NEW
            'Volume': 'volume'
        })
        
        # Force strict column selection
        # If a file is missing a column, fill it with 0 to prevent crashing
        for col in EXPECTED_COLS:
            if col not in df.columns:
                df[col] = 0
                
        df = df[EXPECTED_COLS]
        data_frames.append(df)
        
    except Exception as e:
        print(f"Skipping {filename}: {e}")

print(f"Loaded {len(data_frames)} stocks from folder.")

# ==========================================
# DOWNLOAD MEME STOCKS FROM YAHOO FINANCE (One by One)
# ==========================================
print("\n--- Downloading Meme Stocks ---")

for ticker in MEME_TICKERS:
    print(f"Downloading {ticker}...")
    
    # Download ONE ticker at a time to avoid MultiIndex headers
    df = yf.download(ticker, start=START_DATE, end=END_DATE, progress=False, auto_adjust=False)
    
    if df.empty:
        print(f"Warning: No data found for {ticker}")
        continue

    # Reset index (Date moves from Index to Column)
    df = df.reset_index()
    
    # Flatten Columns
    # If yfinance returns MultiIndex columns, we drop the top level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Add Ticker Column
    df['ticker'] = ticker
    
    # Rename to match standard
    # yfinance (auto_adjust=True) returns: Date, Open, High, Low, Close, Volume
    df = df.rename(columns={
        'Date': 'date',
        'Open': 'open_price',
        'Close': 'close_price',
        'High': 'high_price', # NEW
        'Low': 'low_price',   # NEW
        'Volume': 'volume'
    })
    
    # Select only expected columns
    df = df[EXPECTED_COLS]
    
    data_frames.append(df)
    print(f"Added {len(df)} rows for {ticker}")

# ==========================================
# MERGE & SAVE
# ==========================================
print("\n--- Merging Data ---")
if not data_frames:
    print("Error: No data collected!")
else:
    # Concatenate all dataframes
    final_df = pd.concat(data_frames, ignore_index=True)

    # Ensure dates are proper format
    final_df['date'] = pd.to_datetime(final_df['date']).dt.date
    
    # Filter 2021 Date Range
    start_dt = pd.to_datetime(START_DATE).date()
    end_dt = pd.to_datetime(END_DATE).date()
    final_df = final_df[(final_df['date'] >= start_dt) & (final_df['date'] <= end_dt)]

    # Sort
    final_df = final_df.sort_values(by=['ticker', 'date'])

    # Save
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Success! Saved {len(final_df)} rows to {OUTPUT_FILE}")
    print(final_df.head())