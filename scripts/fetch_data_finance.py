import yfinance as yf
import pandas as pd
import os

TARGET_STOCKS = [
    'AAPL', 'ADBE', 'AMC', 'AMZN', 'CRM', 'CSCO', 'GME', 'GOOG', 
    'GOOGL', 'IBM', 'INTC', 'META', 'MSFT', 'NFLX', 'NVDA', 'ORCL', 'TSLA'
]

DATA_DIR = "../data"

def fetch_and_save_financials():
    print("Fetching Dividends and Splits from Yahoo Finance...")
    
    all_divs = []
    all_splits = []

    for ticker in TARGET_STOCKS:
        print(f"  Processing {ticker}...")
        try:
            # Fetch Ticker Object
            stock = yf.Ticker(ticker)
            
            # 1. Get Dividends
            # Returns a Pandas Series with Date index
            divs = stock.dividends

            # Filter for 2021 only
            divs = divs[(divs.index >= '2021-01-01') & (divs.index <= '2021-12-31')]
            
            for date, amount in divs.items():
                all_divs.append({
                    'ticker': ticker,
                    'ex_date': date.strftime('%Y-%m-%d'),
                    'amount': amount
                })

            # 2. Get Splits
            splits = stock.splits
            # Filter for 2021 only
            splits = splits[(splits.index >= '2021-01-01') & (splits.index <= '2021-12-31')]
            
            for date, ratio in splits.items():
                if 0.9 < ratio < 1.1:
                    print(f"  Skipping probable spinoff adjustment for {ticker}: {ratio}")
                    continue
                all_splits.append({
                    'ticker': ticker,
                    'date': date.strftime('%Y-%m-%d'),
                    'ratio': ratio
                })
                
        except Exception as e:
            print(f"  Error fetching {ticker}: {e}")

    # Save Dividends
    if all_divs:
        df_divs = pd.DataFrame(all_divs)
        div_path = os.path.join(DATA_DIR, "clean_dividends.csv")
        df_divs.to_csv(div_path, index=False)
        print(f"Saved {len(df_divs)} dividends to {div_path}")

    # Save Splits
    if all_splits:
        df_splits = pd.DataFrame(all_splits)
        split_path = os.path.join(DATA_DIR, "clean_stock_splits.csv")
        df_splits.to_csv(split_path, index=False)
        print(f"Saved {len(df_splits)} splits to {split_path}")

if __name__ == "__main__":
    fetch_and_save_financials()