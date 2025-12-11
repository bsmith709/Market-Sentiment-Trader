import csv
import re
import multiprocessing as mp
import time
import os
import glob
from datetime import datetime
from datasets import load_dataset

# ==========================================
# CONFIGURATION
# ==========================================
OUTPUT_FILE = "../data/clean_news_2021.csv"
TEMP_DIR = "../data/temp_headlines"
BATCH_SIZE = 5000  # Number of rows to send to a worker at once
NUM_WORKERS = mp.cpu_count()  # Use all available CPU cores

# 1. Target Tickers
TARGET_TICKERS = {
    'AAPL', 'ADBE', 'AMZN', 'CRM', 'CSCO', 'GOOG', 'GOOGL', 'IBM', 'INTC', 
    'FB', 'META', 'MSFT', 'NFLX', 'NVDA', 'ORCL', 'TSLA', 'GME', 'AMC'
}

# 2. Comprehensive Keyword Map
STOCK_KEYWORDS = {
    'GME': [r'\bgamestop\b', r'\bgme\b', r'\btendies\b', r'\bshort squeeze\b', r'\bdiamond hands\b', r'\broaring kitty\b'],
    'AMC': [r'\bamc\b', r'\bamc theaters\b', r'\bmovie stock\b', r'\bapes\b', r'\bmovie chain\b', r'\bmovie\b'],
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

START_DATE = datetime(2021, 1, 1)
END_DATE = datetime(2021, 12, 31)

# ==========================================
# WORKER FUNCTION (CPU BOUND)
# ==========================================
def worker_process(input_queue, worker_id):
    """
    Consumes batches of raw rows, processes them, and puts valid rows into output_queue.
    """
    # Create temp filename unique to this worker
    temp_filepath = os.path.join(TEMP_DIR, f"part_{worker_id}.csv")

    with open(temp_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        while True:
            batch = input_queue.get()
            if batch is None:  # Poison pill to stop
                break

            processed_batch = []
            
            for row in batch:
                try:
                    # --- STEP 1: DATE FILTER (Fastest check) ---
                    try:
                        article_date = datetime.fromisoformat(str(row['Date'])[:10])
                    except (ValueError, TypeError):
                        continue

                    if not (START_DATE <= article_date <= END_DATE):
                        continue

                    # --- 2. Strict Ticker Verification ---
                    final_ticker = None
                    headline = str(row['Article_title']).lower()
                    
                    # Option A: Dataset Suggestion
                    dataset_ticker = str(row['Stock_symbol']).strip().upper()
                    
                    # If dataset suggests a target, we MUST verify it in the text
                    if dataset_ticker in TARGET_TICKERS:
                        patterns = STOCK_KEYWORDS[dataset_ticker]
                        for p in patterns:
                            if re.search(p, headline):
                                final_ticker = dataset_ticker
                                break
                    
                    # Option B: Rescue (If Option A failed or dataset was wrong)
                    # If the dataset was wrong (e.g. said AMC but headline says Apple),
                    # we scan for other keywords to save the article.
                    if not final_ticker:
                        for ticker, patterns in STOCK_KEYWORDS.items():
                            for p in patterns:
                                if re.search(p, headline):
                                    final_ticker = ticker
                                    break
                            if final_ticker: break

                    if not final_ticker:
                        continue

                    # --- STEP 3: WRITE ROW ---
                    writer.writerow([
                        article_date.date(),
                        row['Article_title'],
                        row['Publisher'],
                        row['Url'],
                        final_ticker
                    ])

                except Exception:
                    continue
        

# ==========================================
# MERGE FUNCTION
# ==========================================
def merge_temp_files(final_path):
    print("\nMerging temporary files...")
    temp_files = glob.glob(os.path.join(TEMP_DIR, "part_*.csv"))
    global_id = 0
    
    with open(final_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(['article_id', 'date', 'headline', 'source', 'url', 'ticker'])  # Header
        
        for temp_file in temp_files:
            with open(temp_file, 'r', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                for row in reader:
                    global_id += 1
                    # 'row' is already a list of strings from the temp file
                    writer.writerow([global_id] + row)
            os.remove(temp_file)
            
    print(f"Merge complete. Total articles: {global_id}")

# ==========================================
# MAIN CONTROLLER
# ==========================================
if __name__ == "__main__":
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    print(f"Starting parallel processing with {NUM_WORKERS} workers...")
    start_time = time.time()
    
    # Create Queues
    input_queue = mp.Queue(maxsize=100) # Buffer size to prevent memory overflow
    
    # Start Worker Processes
    workers = []
    for i in range(NUM_WORKERS):
        p = mp.Process(target=worker_process, args=(input_queue, i))
        p.start()
        workers.append(p)
    
    # Start Streaming from Hugging Face
    print("Initializing stream...")
    ds = load_dataset(
        "Zihan1004/FNSPID", 
        data_files="Stock_news/nasdaq_exteral_data.csv",
        split="train", 
        streaming=True
    )
    
    # Feed the Workers
    batch = []
    total_scanned = 0
    
    for row in ds:
        batch.append(row)
        total_scanned += 1
        
        if len(batch) >= BATCH_SIZE:
            input_queue.put(batch)
            batch = []
            
        if total_scanned % 200000 == 0:
            print(f"Streamed {total_scanned} rows to workers...")

    # Send remaining buffer
    if batch:
        input_queue.put(batch)
        
    # Send Poison Pills to stop workers
    for _ in range(NUM_WORKERS):
        input_queue.put(None)
        
    # Wait for workers to finish
    for p in workers:
        p.join()
        
    # Merge temp files
    merge_temp_files(OUTPUT_FILE)
    
    print(f"Job Complete in {round(time.time() - start_time, 2)} seconds.")