from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, TIMESTAMP, Enum, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB  # Specific import for Postgres JSON
from database import Base
import enum

# ==========================================
# ENUMS (Must match SQL types exactly)
# ==========================================
class SentimentType(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class TradeAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"

# ==========================================
# GROUP A: REFERENCE & PUBLIC DATA
# ==========================================

class Stock(Base):
    __tablename__ = "stocks"

    ticker = Column(String, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    sector = Column(String)

    # Relationships
    prices = relationship("StockPrice", back_populates="stock")
    dividends = relationship("Dividend", back_populates="stock")
    splits = relationship("StockSplit", back_populates="stock")
    news_mentions = relationship("NewsSentiment", back_populates="stock")
    reddit_mentions = relationship("RedditSentiment", back_populates="stock")
    daily_scores = relationship("DailySentimentScore", back_populates="stock")

class StockPrice(Base):
    __tablename__ = "stock_prices"

    price_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(Numeric(14, 2))
    close_price = Column(Numeric(14, 2))
    volume = Column(Integer)

    stock = relationship("Stock", back_populates="prices")

class Dividend(Base):
    __tablename__ = "dividends"
    dividend_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    ex_date = Column(Date, nullable=False)
    amount = Column(Numeric(10, 4), nullable=False)

    stock = relationship("Stock", back_populates="dividends")

class StockSplit(Base):
    __tablename__ = "stock_splits"
    split_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    ratio = Column(Numeric(10, 4), nullable=False)

    stock = relationship("Stock", back_populates="splits")

class MarketHoliday(Base):
    __tablename__ = "market_holidays"
    date = Column(Date, primary_key=True)
    name = Column(String)

class NewsArticle(Base):
    __tablename__ = "news_articles"

    article_id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    headline = Column(String, nullable=False)
    source = Column(String)
    url = Column(String)

    mentions = relationship("NewsSentiment", back_populates="article")

class RedditPost(Base):
    __tablename__ = "reddit_posts"

    post_id = Column(String, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    title = Column(String, nullable=False)
    body = Column(String)
    score = Column(Integer)
    comment_count = Column(Integer)

    mentions = relationship("RedditSentiment", back_populates="post")

# ==========================================
# GROUP B: SENTIMENT (BRIDGES)
# ==========================================

class NewsSentiment(Base):
    __tablename__ = "news_sentiment_mentions"

    mention_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    article_id = Column(Integer, ForeignKey("news_articles.article_id"), nullable=False)
    sentiment_label = Column(Enum(SentimentType))
    confidence_score = Column(Numeric(5, 4))

    stock = relationship("Stock", back_populates="news_mentions")
    article = relationship("NewsArticle", back_populates="mentions")

class RedditSentiment(Base):
    __tablename__ = "reddit_sentiment_mentions"

    mention_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    post_id = Column(String, ForeignKey("reddit_posts.post_id"), nullable=False)
    sentiment_label = Column(Enum(SentimentType))
    confidence_score = Column(Numeric(5, 4))

    stock = relationship("Stock", back_populates="reddit_mentions")
    post = relationship("RedditPost", back_populates="mentions")

class DailySentimentScore(Base):
    __tablename__ = "daily_sentiment_aggregates"
    ticker = Column(String, ForeignKey("stocks.ticker"), primary_key=True)
    date = Column(Date, primary_key=True)
    news_score = Column(Numeric(5, 4))
    reddit_score = Column(Numeric(5, 4))
    
    stock = relationship("Stock", back_populates="daily_scores")

# ==========================================
# GROUP C: APP LOGIC (USERS & BACKTESTS)
# ==========================================

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)

    strategies = relationship("Strategy", back_populates="owner")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="user")

class Strategy(Base):
    __tablename__ = "strategies"

    strategy_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # JSONB is crucial for storing flexible rules
    rules = Column(JSONB)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

    owner = relationship("User", back_populates="strategies")
    jobs = relationship("BacktestJob", back_populates="strategy", cascade="all, delete-orphan")
    leaderboard_entries = relationship("LeaderboardEntry", back_populates="strategy", cascade="all, delete-orphan")

class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    job_id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.strategy_id"), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.pending)
    submitted_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    completed_at = Column(TIMESTAMP, nullable=True)

    strategy = relationship("Strategy", back_populates="jobs")
    result = relationship("BacktestResult", back_populates="job", uselist=False, cascade="all, delete-orphan")

class BacktestResult(Base):
    __tablename__ = "backtest_results"

    result_id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("backtest_jobs.job_id"), nullable=False)
    total_return_pct = Column(Numeric(10, 2))
    win_rate = Column(Numeric(5, 2))
    max_drawdown_pct = Column(Numeric(10, 2))

    job = relationship("BacktestJob", back_populates="result")
    trades = relationship("TradeLog", back_populates="result", cascade="all, delete-orphan")
    leaderboard_entry = relationship("LeaderboardEntry", back_populates="backtest", uselist=False, cascade="all, delete-orphan")

class TradeLog(Base):
    __tablename__ = "trade_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer, ForeignKey("backtest_results.result_id"), nullable=False)
    ticker = Column(String, ForeignKey("stocks.ticker"), nullable=False)
    action = Column(Enum(TradeAction, name="trade_action"), nullable=False)
    date = Column(Date, nullable=False)
    price = Column(Numeric(14, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    profit = Column(Numeric(14, 2), nullable=True)

    result = relationship("BacktestResult", back_populates="trades")

class LeaderboardEntry(Base):
    __tablename__ = "leaderboard"
    entry_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.strategy_id"), nullable=False)
    backtest_id = Column(Integer, ForeignKey("backtest_results.result_id"), nullable=False)
    
    total_return_pct = Column(Numeric(10, 2), nullable=False)
    rank_date = Column(Date, server_default=text("CURRENT_DATE"))

    user = relationship("User", back_populates="leaderboard_entries")
    strategy = relationship("Strategy", back_populates="leaderboard_entries")
    backtest = relationship("BacktestResult", back_populates="leaderboard_entry")