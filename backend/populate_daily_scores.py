import models
from database import SessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy import func
import datetime

def calculate_news_hype(mentions):
    """
    Standard confidence-weighted average.
    """
    if not mentions:
        return 0.5
    
    numerator = 0.0
    denominator = 0.0
    
    for m in mentions:
        if m.sentiment_label == models.SentimentType.positive:
            val = 1.0
        elif m.sentiment_label == models.SentimentType.neutral:
            val = 0.5
        else: # negative
            val = 0.0
            
        weight = float(m.confidence_score)
        
        numerator += (val * weight)
        denominator += weight
        
    return (numerator / denominator) if denominator > 0 else 0.5

def calculate_reddit_hype(mentions):
    """
    Advanced Impact-Weighted average.
    Weight = Confidence * (Score / (Comments + 1))
    """
    if not mentions:
        return 0.5
    
    numerator = 0.0
    denominator = 0.0
    
    for m in mentions:
        post = m.post # Joined Relationship
        
        # 1. Sentiment Value (0.0 to 1.0)
        if m.sentiment_label == models.SentimentType.positive:
            val = 1.0
        elif m.sentiment_label == models.SentimentType.neutral:
            val = 0.5
        else: # negative
            val = 0.0
            
        # 2. Calculate Impact Metric
        # Avoid negative scores messing up the math
        safe_score = max(0, post.score) 
        
        # Ratio: High Score + Low Comments = High Impact
        impact = safe_score / (post.comment_count + 1)
        
        # 3. Final Weight
        # We multiply confidence by impact. 
        # A 99% confident bot post with 0 upvotes gets 0 weight.
        # A 60% confident viral post gets massive weight.
        weight = float(m.confidence_score) * impact
        
        numerator += (val * weight)
        denominator += weight
        
    return (numerator / denominator) if denominator > 0 else 0.5

def run_etl():
    db = SessionLocal()
    print("Starting Daily Score ETL...")
    
    try:
        # 1. Clear Old Data
        print("Clearing old aggregates...")
        db.query(models.DailySentimentScore).delete()
        db.commit()
        
        # 2. Get Scope (Dates and Tickers)
        # We only care about 2021 dates present in our raw data
        # Optimization: Fetch distinct dates from stock_prices
        dates = db.query(models.StockPrice.date).distinct().all()
        dates = [d[0] for d in dates] # Flatten tuple
        
        tickers = db.query(models.Stock.ticker).all()
        tickers = [t[0] for t in tickers]
        
        total_ops = len(dates) * len(tickers)
        current_op = 0
        
        print(f"Processing {len(tickers)} stocks across {len(dates)} days...")
        
        batch = []
        
        for sim_date in dates:
            # OPTIMIZATION: Fetch all mentions for this DAY in one go
            # (Instead of querying inside the loop 18 times)
            
            # Fetch News
            day_news = db.query(models.NewsSentiment)\
                .options(joinedload(models.NewsSentiment.article))\
                .join(models.NewsArticle)\
                .filter(models.NewsArticle.date == sim_date)\
                .all()
                
            # Fetch Reddit (Include Post data for score/comments)
            day_reddit = db.query(models.RedditSentiment)\
                .options(joinedload(models.RedditSentiment.post))\
                .join(models.RedditPost)\
                .filter(models.RedditPost.date == sim_date)\
                .all()
            
            # Group by Ticker in Python (Memory is cheap, DB roundtrips are expensive)
            news_map = {t: [] for t in tickers}
            reddit_map = {t: [] for t in tickers}
            
            for n in day_news:
                if n.ticker in news_map: news_map[n.ticker].append(n)
            
            for r in day_reddit:
                if r.ticker in reddit_map: reddit_map[r.ticker].append(r)
            
            # Calculate Scores
            for ticker in tickers:
                n_mentions = news_map[ticker]
                r_mentions = reddit_map[ticker]
                
                # Only save row if there is data
                if not n_mentions and not r_mentions:
                    continue
                
                n_score = calculate_news_hype(n_mentions)
                r_score = calculate_reddit_hype(r_mentions)
                
                # Count mentions (Optional, for significance checks later)
                count = len(n_mentions) + len(r_mentions)
                
                agg = models.DailySentimentScore(
                    ticker=ticker,
                    date=sim_date,
                    news_score=n_score,
                    reddit_score=r_score,
                    mention_count=count
                )
                batch.append(agg)
            
            current_op += len(tickers)
            if len(batch) > 1000:
                db.add_all(batch)
                db.commit()
                batch = []
                print(f"Processed {sim_date}...")
                
        if batch:
            db.add_all(batch)
            db.commit()
            
        print("ETL Complete. Daily scores populated.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_etl()