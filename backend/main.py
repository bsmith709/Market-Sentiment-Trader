from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import timedelta, date, datetime
from typing import List
import bcrypt
import models, schemas, database
from jose import JWTError, jwt
from fastapi.middleware.cors import CORSMiddleware

# --- CONFIG ---
SECRET_KEY = "CHANGE_THIS_TO_A_RANDOM_SECRET_STRING"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- SETUP ---
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI()
# Allow Swagger (and eventually SvelteKit) to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Security & Hashing
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- UTILITIES (AUTH) ---
def verify_password(plain_password, hashed_password):
    plain_password_bytes = plain_password.encode('utf-8')
    hashed_password_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)

def get_password_hash(password):
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency: Get Current User
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ROUTES ---

@app.post("/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    # Check if user exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = models.User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # Verify user
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- TICKER DASHBOARD ROUTES ---

@app.get("/stocks", response_model=List[schemas.StockDashboardRow])
def get_dashboard_stocks(
    sim_date: date, # User MUST provide a date (e.g., ?sim_date=2023-01-01)
    db: Session = Depends(database.get_db)
):
    """
    Optimized: Fetches Stock + Price + Pre-calculated Scores in ONE query.
    """
    return db.query(
        models.Stock.ticker,
        models.Stock.company_name,
        models.Stock.sector,
        models.StockPrice.open_price.label("daily_open"),
        models.StockPrice.close_price.label("daily_close"),
        models.StockPrice.volume.label("daily_volume"),
        func.coalesce(models.DailySentimentScore.news_score, 0.5).label("news_hype_score"),
        func.coalesce(models.DailySentimentScore.reddit_score, 0.5).label("reddit_hype_score")
    ).join(models.StockPrice, models.Stock.ticker == models.StockPrice.ticker)\
     .outerjoin(models.DailySentimentScore, 
        (models.DailySentimentScore.ticker == models.Stock.ticker) & 
        (models.DailySentimentScore.date == sim_date)
     )\
     .filter(models.StockPrice.date == sim_date)\
     .all()

@app.get("/stocks/{ticker}", response_model=schemas.StockDetailWithHistory)
def get_stock_detail(ticker: str, db: Session = Depends(database.get_db)):
    # Fetch the stock
    stock = db.query(models.Stock).filter(models.Stock.ticker == ticker).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Fetch All Raw Data (Prices, News, Reddit) associated with this ticker
    prices = db.query(models.StockPrice).filter(models.StockPrice.ticker == ticker).all()
    
    # Fetch Pre-Calculated Scores
    scores = db.query(models.DailySentimentScore).filter(models.DailySentimentScore.ticker == ticker).all()
    
    history_map = {}
    
    # Initialize with Prices
    for p in prices:
        history_map[p.date] = {
            "close_price": p.close_price,
            "daily_volume": p.volume,
            "news_hype_score": 0.5,   # Default
            "reddit_hype_score": 0.5  # Default
        }

    # Overlay Scores
    for s in scores:
        if s.date in history_map:
            history_map[s.date]["news_hype_score"] = float(s.news_score) if s.news_score is not None else 0.5
            history_map[s.date]["reddit_hype_score"] = float(s.reddit_score) if s.reddit_score is not None else 0.5

    # 5. Flatten to List
    history_list = []
    for d in sorted(history_map.keys()):
        data = history_map[d]
        history_list.append(schemas.DailyStockStats(
            date=d,
            close_price=data["close_price"],
            daily_volume=data["daily_volume"],
            news_hype_score=data["news_hype_score"],
            reddit_hype_score=data["reddit_hype_score"]
        ))

    return schemas.StockDetailWithHistory(
        ticker=stock.ticker,
        company_name=stock.company_name,
        sector=stock.sector,
        history=history_list
    )

# --- STRATEGY & BACKTEST ROUTES ---

@app.post("/strategies", response_model=schemas.StrategyOut)
def create_strategy(
    strategy: schemas.StrategyCreate, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    
    # --- VALIDATION ---

    # Extract tickers from the request
    requested_tickers = {rule.ticker for rule in strategy.rules}
    
    # Query DB to find which of these actually exist
    valid_stocks = db.query(models.Stock.ticker)\
        .filter(models.Stock.ticker.in_(requested_tickers))\
        .all()
    
    # Flatten list of tuples [('AAPL',), ('TSLA',)] -> {'AAPL', 'TSLA'}
    valid_tickers_set = {s[0] for s in valid_stocks}
    
    # Find the difference
    invalid_tickers = requested_tickers - valid_tickers_set
    
    if invalid_tickers:
        raise HTTPException(
            status_code=400, 
            detail=f"The following tickers do not exist in the database: {invalid_tickers}"
        )
        
    # --- END VALIDATION ---


    # Convert Pydantic list of rules -> JSON-compatible list of dicts
    rules_data = [rule.dict() for rule in strategy.rules]

    new_strategy = models.Strategy(
        user_id=current_user.user_id,
        name=strategy.name,
        description=strategy.description,
        rules=rules_data, # Store everything here
    )
    db.add(new_strategy)
    db.commit()
    db.refresh(new_strategy)
    return new_strategy

@app.get("/strategies", response_model=List[schemas.StrategyOut])
def get_my_strategies(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    return db.query(models.Strategy).filter(models.Strategy.user_id == current_user.user_id).all()

# --- BACKTEST EXECUTION ---

def run_backtest_logic(job_id: int, db: Session):
    """
    Simulates the backtest. Later I will integrate the backtest engine here.
    """
    import time
    import random
    
    print(f"Starting job {job_id}...")
    time.sleep(5) # Simulate processing time
    
    # 1. Fetch Job
    job = db.query(models.BacktestJob).get(job_id)
    if not job:
        return

    # 2. Simulate Result (Replace this with real engine logic later)
    # This logic would actually use the strategy.buy_rules_json to check stock prices
    try:
        total_return = random.uniform(-10, 20)
        
        # Create Result Record
        result = models.BacktestResult(
            job_id=job.job_id,
            total_return_pct=total_return,
            win_rate=random.uniform(0.4, 0.7),
            max_drawdown_pct=random.uniform(-5, -20)
        )
        db.add(result)
        
        # Update Job Status
        job.status = models.JobStatus.completed
        job.completed_at = datetime.utcnow()
        db.commit()
        print(f"Job {job_id} completed.")
        
    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        job.status = models.JobStatus.failed
        db.commit()

@app.post("/backtest/{strategy_id}", response_model=schemas.BacktestJobOut)
def submit_backtest(
    strategy_id: int, 
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # Verify strategy ownership
    strategy = db.query(models.Strategy).filter(
        models.Strategy.strategy_id == strategy_id, 
        models.Strategy.user_id == current_user.user_id
    ).first()
    
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # Create Job
    new_job = models.BacktestJob(strategy_id=strategy.strategy_id, status=models.JobStatus.pending)
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Hand off to background task
    background_tasks.add_task(run_backtest_logic, new_job.job_id, db)

    return new_job

@app.get("/backtest/jobs", response_model=List[schemas.BacktestJobOut])
def get_backtest_jobs(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    # Join Strategy to filter by user
    jobs = db.query(models.BacktestJob).join(models.Strategy).filter(
        models.Strategy.user_id == current_user.user_id
    ).all()
    return jobs