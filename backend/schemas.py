from pydantic import BaseModel, EmailStr
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
    email: EmailStr

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
    email: Optional[str] = None

# --- STOCK DASHBOARD SCHEMAS ---
class StockPriceOut(BaseModel):
    date: date
    close_price: float
    volume: int
    class Config:
        from_attributes = True

class SentimentOut(BaseModel):
    sentiment_label: SentimentType
    confidence_score: float
    # We might want to link back to the article/post title here
    class Config:
        from_attributes = True

class StockDetailOut(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str]
    # Include recent data for the dashboard charts
    recent_prices: List[StockPriceOut] = []
    
    class Config:
        from_attributes = True

# --- STRATEGY & BACKTEST SCHEMAS ---
class StrategyBase(BaseModel):
    name: str
    buy_rules_json: Dict[str, Any] 
    sell_rules_json: Dict[str, Any]

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