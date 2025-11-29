import psycopg2
import os
import csv
import pandas as pd
from io import StringIO

# ==========================================
# CONFIGURATION
# ==========================================
DATABASE_URL = "postgresql://postgres@localhost/sentiment_db"
DATA_DIR = "../data"

# File mappings
STOCKS_FILE = "clean_stock_prices_2021.csv" # We extract unique tickers from here
NEWS_FILE = "clean_news_2021.csv"
REDDIT_FILE = "clean_reddit_2021.csv"
NEWS_SENTIMENT_FILE = "ready_news_sentiment.csv"
REDDIT_SENTIMENT_FILE = "ready_reddit_sentiment.csv"

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_conn():
    return psycopg2.connect(DATABASE_URL)

def reset_database(cur):
    """
    Clears out existing data to avoid 'Duplicate Key' errors.
    Uses CASCADE to ensure linked tables (like sentiment mentions) are cleared too.
    """
    print("Cleaning old data...")
    tables = [
        "trade_logs",
        "backtest_results",
        "backtest_jobs",
        "news_sentiment_mentions",
        "reddit_sentiment_mentions",
        "stock_prices",
        "news_articles",
        "reddit_posts"
    ]
    
    for table in tables:
        # TRUNCATE is faster than DELETE and resets valid_ids if needed
        # RESTART IDENTITY resets any auto-increment counters
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
    
    print("Database clean. Ready to load.")

def populate_stocks_table(cur):
    """
    Populates the 'stocks' reference table.
    """
    print("Populating 'stocks' table...")
    
    # 16 Target Stocks
    stocks_data = [
        ('AAPL', 'Apple Inc.', 'Technology'),
        ('ADBE', 'Adobe Inc.', 'Technology'),
        ('AMC', 'AMC Entertainment', 'Communication Services'),
        ('AMZN', 'Amazon.com', 'Consumer Cyclical'),
        ('CRM', 'Salesforce', 'Technology'),
        ('CSCO', 'Cisco Systems', 'Technology'),
        ('GME', 'GameStop Corp.', 'Consumer Cyclical'),
        ('GOOG', 'Alphabet Inc.', 'Technology'),
        ('GOOGL', 'Alphabet Inc.', 'Technology'),
        ('IBM', 'IBM', 'Technology'),
        ('INTC', 'Intel Corp.', 'Technology'),
        ('META', 'Meta Platforms', 'Technology'),
        ('MSFT', 'Microsoft Corp.', 'Technology'),
        ('NFLX', 'Netflix Inc.', 'Communication Services'),
        ('NVDA', 'Nvidia Corp.', 'Technology'),
        ('ORCL', 'Oracle Corp.', 'Technology'),
        ('TSLA', 'Tesla Inc.', 'Consumer Cyclical')
    ]
    
    # Insert ignore (ON CONFLICT DO NOTHING) to avoid duplicates if you run this twice
    insert_query = """
        INSERT INTO stocks (ticker, company_name, sector)
        VALUES (%s, %s, %s)
        ON CONFLICT (ticker) DO NOTHING;
    """
    
    cur.executemany(insert_query, stocks_data)
    print(f"Inserted/Verified {len(stocks_data)} stocks.")

def bulk_copy(cur, file_path, table_name, columns, valid_ids_filter=None, filter_col=None):
    """
    Uses Postgres COPY command for massive speed (much faster than INSERT).
    """
    full_path = os.path.join(DATA_DIR, file_path)
    
    if not os.path.exists(full_path):
        print(f"Warning: {full_path} not found. Skipping {table_name}.")
        return

    print(f"Loading {table_name} from {file_path}...")
    
    # Use Pandas to handle CSV parsing (handling quotes, newlines, etc.)
    # and verify columns match before streaming to DB.
    try:
        # Read CSV
        df = pd.read_csv(full_path)

        # --- Specific Cleaning Rules ---
        if table_name == 'reddit_posts':
            # Drop rows with empty titles
            initial_len = len(df)
            df = df.dropna(subset=['title'])
            df = df[df['title'].str.strip() != '']
            if len(df) < initial_len:
                print(f"   -> Filtered {initial_len - len(df)} posts with empty titles.")

        # --- Foreign Key Filtering ---
        if valid_ids_filter is not None and filter_col is not None:
            initial_len = len(df)
            # Only keep rows where the foreign key exists in our valid set
            df = df[df[filter_col].isin(valid_ids_filter)]
            print(f"   -> Filtered {initial_len - len(df)} orphaned sentiment rows.")
        
        # Select ONLY the columns we want to insert (matches DB schema)
        # This fixes issues where the CSV has extra columns (like 'ticker' in news)
        df = df[columns]
        
        # Create a string buffer
        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)
        
        # Copy to DB
        # This is the "Magic" PostgreSQL command
        cur.copy_expert(f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH CSV", buffer)
        print(f"Success: Loaded {len(df)} rows into {table_name}.")

        # Return Primary Keys for future filtering
        if table_name == 'reddit_posts':
            return set(df['post_id'].unique())
        
    except Exception as e:
        print(f"Error loading {table_name}: {e}")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        reset_database(cur)
        
        # 1. Stocks (Must be first for Foreign Keys)
        populate_stocks_table(cur)
        
        # 2. Stock Prices
        # CSV cols: ticker, date, open_price, close_price, volume
        # Table cols: (id auto), ticker, date, open_price, close_price, volume
        bulk_copy(cur, STOCKS_FILE, 'stock_prices', 
                 ['ticker', 'date', 'open_price', 'close_price', 'volume'])
        
        # 3. News Articles
        # CSV has: article_id, date, headline, source, url, ticker
        # Table needs: article_id, date, headline, source, url
        # We explicitly select ONLY the 5 cols the table needs
        bulk_copy(cur, NEWS_FILE, 'news_articles', 
                 ['article_id', 'date', 'headline', 'source', 'url'])
        
        # 4. Reddit Posts (Capture valid IDs)
        valid_post_ids = bulk_copy(cur, REDDIT_FILE, 'reddit_posts', 
                 ['post_id', 'date', 'title', 'body', 'score', 'comment_count'])
        
        # 5. Sentiment Tables (The Bridge)
        # News Sentiment
        # Table: mention_id (auto), article_id, ticker, sentiment_label, confidence_score
        bulk_copy(cur, NEWS_SENTIMENT_FILE, 'news_sentiment_mentions', 
                 ['article_id', 'ticker', 'sentiment_label', 'confidence_score'])
        
        # Reddit Sentiment
        # Table: mention_id (auto), post_id, ticker, sentiment_label, confidence_score
        bulk_copy(cur, REDDIT_SENTIMENT_FILE, 'reddit_sentiment_mentions', 
                 ['post_id', 'ticker', 'sentiment_label', 'confidence_score'],
                 valid_ids_filter=valid_post_ids, filter_col='post_id')

        conn.commit()
        print("Database Population Complete!")
        
    except Exception as e:
        print(f"Critical Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()