import pandas as pd
import re
import os

# ==========================================
# CONFIGURATION
# ==========================================
NEWS_INPUT_FILE = "../data/clean_news_2021.csv"
REDDIT_INPUT_FILE = "../data/clean_reddit_2021.csv"

NEWS_OUTPUT_FILE = "../data/news_sentiment_inputs.csv"
REDDIT_OUTPUT_FILE = "../data/reddit_sentiment_inputs.csv"

# Keyword matching dictionary
STOCK_KEYWORDS = {
    # The Meme Stock Test Group
    'GME': [r'\bgamestop\b', r'\bgme\b', r'\btendies\b', r'\bshort squeeze\b', r'\bdiamond hands\b', r'\broaring kitty\b'],
    'AMC': [r'\bamc\b', r'\bamc theaters\b', r'\bmovie stock\b', r'\bapes\b', r'\bmovie chain\b', r'\bmovie\b'],

    # The Tech Giant Control Group
    'AAPL': [r'\bapple\b', r'\baapl\b', r'\biphone\b', r'\bmacbook\b', r'\btim cook\b'],
    'MSFT': [r'\bmicrosoft\b', r'\bmsft\b', r'\bsatya nadella\b', r'\bazure\b', r'\bwindows\b'],
    'AMZN': [r'\bamazon\b', r'\bamzn\b', r'\bbezos\b', r'\bprime\b', r'\baws\b', r'\bamazon prime\b'],
    'TSLA': [r'\btesla\b', r'\btsla\b', r'\belon musk\b', r'\bev\b', r'\bmodel 3\b', r'\bcybertruck\b', r'\bspacex\b'],
    'GOOGL': [r'\bgoogle\b', r'\bgoogl\b', r'\balphabet\b', r'\bpichai\b', r'\bsearch engine\b'],
    'META': [r'\bmeta\b', r'\bfacebook\b', r'\bfb\b', r'\bzuckerberg\b', r'\binstagram\b', r'\boculus\b', r'\bmetaverse\b'],
    'NVDA': [r'\bnvidia\b', r'\bnvda\b', r'\bgpu\b', r'\bchips\b', r'\bjensen huang\b', r'\bai chips\b'],
    'NFLX': [r'\bnetflix\b', r'\bnflx\b', r'\bstreaming\b', r'\breed hastings\b', r'\bsarandos\b'],
    'ADBE': [r'\badobe\b', r'\badbe\b', r'\bphotoshop\b', r'\billustrator\b', r'\bcreative cloud\b'],
    'CRM': [r'\bsalesforce\b', r'\bcrm\b', r'\bbenioff\b', r'\bslack\b'],
    'CSCO': [r'\bcisco\b', r'\bcsco\b', r'\bwebex\b', r'\bnetworking\b'],
    'INTC': [r'\bintel\b', r'\bintc\b', r'\bchipmaker\b', r'\bprocessors\b', r'\bpat gelsinger\b'],
    'IBM': [r'\bibm\b', r'\bbig blue\b', r'\bwatson\b', r'\barvind krishna\b'],
    'ORCL': [r'\boracle\b', r'\borcl\b', r'\blarry ellison\b', r'\bdatabases\b'],
}

# ==========================================
# CLEANING FUNCTION (Entity Extraction)
# ==========================================
def find_mentioned_tickers(text, keyword_map):
    """
    Scans text for keywords and returns a list of mentioned tickers.
    Uses word boundaries (\b) to prevent false matches (e.g. 'GM' inside 'GMAIL').
    """
    if not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    mentioned = set()

    for ticker, keywords in keyword_map.items():
        for patten in keywords:
            if re.search(patten, text_lower):
                mentioned.add(ticker)
                break  # No need to check other keywords for this ticker
    
    return list(mentioned)

if __name__ == "__main__":
    # --- PART 1: PROCESS REDDIT (Needs Search) ---
    print(f"Loading Reddit data from {REDDIT_INPUT_FILE}...")
    df_reddit = pd.read_csv(REDDIT_INPUT_FILE)

    reddit_rows = []
    print(f"Scanning {len(df_reddit)} Reddit posts for keywords...")
    for idx, row in df_reddit.iterrows():
        content = str(row['title']) + " " + str(row['body'])
        found_tickers = find_mentioned_tickers(content, STOCK_KEYWORDS)

        for ticker in found_tickers:
            reddit_rows.append({
                'post_id': row['post_id'],
                'ticker': ticker,
                'text_input': content
            })
    
    df_reddit_out = pd.DataFrame(reddit_rows)
    df_reddit_out.to_csv(REDDIT_OUTPUT_FILE, index=False)
    print(f"Success! Generated {len(df_reddit_out)} sentiment tasks for Reddit.")

    # --- PART 2: PROCESS NEWS (Pass-Through) ---
    # We already identified tickers in the previous step (get_fnspid_fast.py)
    # So we just need to format the CSV for the FinBERT script.
    print(f"\nLoading News data from {NEWS_INPUT_FILE}...")
    df_news = pd.read_csv(NEWS_INPUT_FILE)
    
    # We expect 'clean_news_2021.csv' to have columns: article_id, date, headline, source, url, ticker
    # We just need to rename 'headline' to 'text_input' for consistency
    df_news_out = df_news[['article_id', 'ticker', 'headline']].copy()
    df_news_out.columns = ['article_id', 'ticker', 'text_input']
    
    df_news_out.to_csv(NEWS_OUTPUT_FILE, index=False)
    print(f"Success! Generated {len(df_news_out)} sentiment tasks for News.")
    
    print("\nREADY FOR FINBERT.")