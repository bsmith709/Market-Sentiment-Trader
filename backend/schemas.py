from pydantic import BaseModel, field_validator, model_validator
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from enum import Enum

# --- Enums ---
class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class SentimentType(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"

# --- AUTH & USER SCHEMAS ---
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- STOCK DASHBOARD SCHEMAS ---
class StockPriceOut(BaseModel):
    date: date
    open_price: float
    close_price: float
    volume: int
    class Config:
        from_attributes = True

class NewsArticleOut(BaseModel):
    headline: str
    source: Optional[str]
    url: Optional[str]
    class Config:
        from_attributes = True

class RedditPostOut(BaseModel):
    title: str
    body: str
    score: int
    comment_count: int
    class Config:
        from_attributes = True

class NewsMentionOut(BaseModel):
    sentiment_label: SentimentType
    confidence_score: float
    article: NewsArticleOut # <--- Nested Article Info
    class Config:
        from_attributes = True

class RedditMentionOut(BaseModel):
    sentiment_label: SentimentType
    confidence_score: float
    post: RedditPostOut # <--- Nested Post Info
    class Config:
        from_attributes = True

# A lightweight schema. No lists, just simple fields.
class StockDashboardRow(BaseModel):
    ticker: str
    company_name: str
    sector: str
    daily_open: float
    daily_close: float 
    daily_volume: int
    reddit_hype_score: float = 0.5 # Default to neutral
    news_hype_score: float = 0.5

    class Config:
        from_attributes = True

# New Schema for a single point on your graph (One Day)
class DailyStockStats(BaseModel):
    date: date
    close_price: Optional[float] = None
    daily_volume: Optional[int] = None
    news_hype_score: float = 0.5   # Default neutral
    reddit_hype_score: float = 0.5 # Default neutral

    class Config:
        from_attributes = True

class StockDetailWithHistory(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str]
    # Include data for the dashboard charts
    history: List[DailyStockStats] = []
    
    class Config:
        from_attributes = True

class SentimentOut(BaseModel):
    sentiment_label: SentimentType
    confidence_score: float
    # We might want to link back to the article/post title here
    class Config:
        from_attributes = True

# --- STRATEGY & BACKTEST SCHEMAS ---
class StrategyRule(BaseModel):
    ticker: str

    max_allocation_pct: float = 0.2

    news_buy_threshold: Optional[float] = None
    news_sell_threshold: Optional[float] = None
    
    reddit_buy_threshold: Optional[float] = None
    reddit_sell_threshold: Optional[float] = None

    # Validator: ensure max_allocation_pct between 0.01 and 1.0
    @field_validator('max_allocation_pct')
    @classmethod
    def check_pct(cls, v):
        if not (0.01 <= v <= 1.0):
            raise ValueError("Max allocation must be between 1% (0.01) and 100% (1.0)")
        return v
    
    # Validator: Check Ranges (0 to 1) only if value is provided
    @field_validator('news_buy_threshold', 'news_sell_threshold', 
                     'reddit_buy_threshold', 'reddit_sell_threshold')
    @classmethod
    def check_range(cls, v: Optional[float]):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Thresholds must be between 0.0 and 1.0')
        return v

    # Validator: Logic Check (Prevent "Do Nothing" rules)
    @model_validator(mode='after')
    def check_at_least_one_trigger(self):
        # A rule must have at least one BUY trigger
        if self.news_buy_threshold is None and self.reddit_buy_threshold is None:
            raise ValueError(f"Ticker {self.ticker}: You must set at least one BUY threshold (News or Reddit).")
        
        # A rule must have at least one SELL trigger
        if self.news_sell_threshold is None and self.reddit_sell_threshold is None:
            raise ValueError(f"Ticker {self.ticker}: You must set at least one SELL threshold (News or Reddit).")
        
        return self

    # Prevent Overlapping Buy/Sell Thresholds
    @model_validator(mode='after')
    def check_logical_consistency(self):
        # Check Reddit Overlap
        if (self.reddit_buy_threshold is not None and 
            self.reddit_sell_threshold is not None):
            
            if self.reddit_buy_threshold <= self.reddit_sell_threshold:
                raise ValueError(
                    f"Ticker {self.ticker}: Reddit Buy Threshold ({self.reddit_buy_threshold}) "
                    f"must be higher than Sell Threshold ({self.reddit_sell_threshold}) "
                    "to prevent infinite trading loops."
                )

        # Check News Overlap
        if (self.news_buy_threshold is not None and 
            self.news_sell_threshold is not None):
            
            if self.news_buy_threshold <= self.news_sell_threshold:
                raise ValueError(
                    f"Ticker {self.ticker}: News Buy Threshold ({self.news_buy_threshold}) "
                    f"must be higher than Sell Threshold ({self.news_sell_threshold}) "
                    "to prevent infinite trading loops."
                )
        return self

class StrategyBase(BaseModel):
    name: str
    description: Optional[str] = None
    rules: List[StrategyRule]
    
    # Validator: Unique Tickers
    @field_validator('rules')
    @classmethod
    def check_duplicate_tickers(cls, rules: List[StrategyRule]):
        tickers = [r.ticker for r in rules]
        if len(tickers) != len(set(tickers)):
            raise ValueError('Duplicate tickers found. Only one rule per stock allowed.')
        return rules

class StrategyCreate(StrategyBase):
    pass

class StrategyOut(StrategyBase):
    strategy_id: int
    user_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TradeLogOut(BaseModel):
    date: date
    action: TradeAction
    ticker: str
    price: float
    quantity: int
    profit: Optional[float]
    class Config:
        from_attributes = True

class BacktestResultOut(BaseModel):
    total_return_pct: float
    win_rate: float
    max_drawdown_pct: float
    trades: List[TradeLogOut] = []
    class Config:
        from_attributes = True

class BacktestJobOut(BaseModel):
    job_id: int
    status: JobStatus
    submitted_at: datetime
    completed_at: Optional[datetime]
    result: Optional[BacktestResultOut] = None # Include result if complete
    class Config:
        from_attributes = True

class LeaderboardOut(BaseModel):
    rank_date: date
    username: str        # We want the name, not the ID
    strategy_name: str
    total_return_pct: float
    
    class Config:
        from_attributes = True

# --- ADMIN SCHEMAS ---

class UserAdminOut(UserOut):
    role: str # 'user' or 'admin'
    # Optional: Count of their strategies (computed field)
    strategy_count: Optional[int] = 0

class StrategyAdminOut(StrategyOut):
    # Admin needs to know who owns the strategy
    owner_username: str 
    
    class Config:
        from_attributes = True

class SystemStats(BaseModel):
    total_users: int
    total_strategies: int
    total_backtests: int
    pending_jobs: int
    total_trades_logged: int