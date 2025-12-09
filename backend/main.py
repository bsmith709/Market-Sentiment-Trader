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
import backtest_engine

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

def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != models.UserRole.admin:
        raise HTTPException(
            status_code=403, 
            detail="Admin privileges required"
        )
    return current_user

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

@app.delete("/admin/users/{user_id}", status_code=204)
def delete_user(
    user_id: int, 
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin) # <--- The Lock
):
    """
    Admin only: Delete a user and all their data (Cascades in DB).
    """
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself (optional safety)
    if user.user_id == admin_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")

    db.delete(user)
    db.commit()
    return None

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
        models.StockPrice.high_price.label("daily_high"),
        models.StockPrice.low_price.label("daily_low"),
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
            open_price=data["open_price"],
            close_price=data["close_price"],
            high_price=data["high_price"],
            low_price=data["low_price"], 
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

@app.delete("/strategies/{strategy_id}", status_code=204)
def delete_strategy(
    strategy_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    User can delete their own strategy.
    """
    strategy = db.query(models.Strategy).filter(
        models.Strategy.strategy_id == strategy_id,
        models.Strategy.user_id == current_user.user_id # <--- Ownership Check
    ).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(strategy)
    db.commit()
    return None

# --- BACKTEST EXECUTION ---
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
    background_tasks.add_task(backtest_engine.run_backtest, new_job.job_id)

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

@app.get("/backtest/results/{job_id}", response_model=schemas.BacktestResultOut)
def get_backtest_result(
    job_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Ensure the Job belongs to the user (via Strategy)
    job = db.query(models.BacktestJob).join(models.Strategy).filter(
        models.BacktestJob.job_id == job_id,
        models.Strategy.user_id == current_user.user_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != models.JobStatus.completed:
        raise HTTPException(status_code=400, detail="Job not completed yet")

    # 2. Return the result (Pydantic will auto-fetch the 'trades' relationship)
    return job.result

@app.get("/leaderboard", response_model=List[schemas.LeaderboardOut])
def get_leaderboard(db: Session = Depends(database.get_db)):
    """
    Returns top performing strategies. 
    Public endpoint (no login required).
    """
    # Join with User and Strategy to get names
    entries = db.query(
        models.LeaderboardEntry.rank_date,
        models.LeaderboardEntry.total_return_pct,
        models.User.username,
        models.Strategy.name.label("strategy_name")
    ).select_from(models.LeaderboardEntry)\
     .join(models.User, models.LeaderboardEntry.user_id == models.User.user_id)\
     .join(models.Strategy, models.LeaderboardEntry.strategy_id == models.Strategy.strategy_id)\
     .order_by(models.LeaderboardEntry.total_return_pct.desc())\
     .limit(10)\
     .all()
     
    return entries

@app.get("/admin/users", response_model=List[schemas.UserAdminOut])
def list_all_users(
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    """
    List all users with their strategy counts.
    """
    # SQL Query: SELECT u.*, COUNT(s.strategy_id) FROM users u LEFT JOIN strategies s ...
    users = db.query(
        models.User,
        func.count(models.Strategy.strategy_id).label("strategy_count")
    ).outerjoin(models.Strategy)\
     .group_by(models.User.user_id)\
     .all()
    
    # Map results to Schema
    results = []
    for user, count in users:
        # Create schema manually or use unpacking if fields match perfectly
        u_out = schemas.UserAdminOut(
            user_id=user.user_id,
            username=user.username,
            created_at=user.created_at,
            role=user.role.value,
            strategy_count=count
        )
        results.append(u_out)
    
    return results

@app.get("/admin/strategies", response_model=List[schemas.StrategyAdminOut])
def list_all_strategies(
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    """
    List ALL strategies (not just own) with owner info.
    """
    # Join with User to get usernames
    strategies = db.query(models.Strategy).options(joinedload(models.Strategy.owner)).all()
    
    results = []
    for s in strategies:
        # Map DB JSON -> Schema List (Same logic as create_strategy)
        results.append(schemas.StrategyAdminOut(
            strategy_id=s.strategy_id,
            user_id=s.user_id,
            name=s.name,
            description=s.description,
            created_at=s.created_at,
            rules=s.rules, 
            owner_username=s.owner.username # <--- The extra field
        ))
    return results

@app.delete("/admin/strategies/{strategy_id}", status_code=204)
def delete_any_strategy(
    strategy_id: int,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    """
    Moderation: Delete ANY strategy by ID (Admin Override).
    """
    strategy = db.query(models.Strategy).filter(models.Strategy.strategy_id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(strategy)
    db.commit()
    return None

@app.get("/admin/stats", response_model=schemas.SystemStats)
def get_system_stats(
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    """
    Dashboard metrics for the Admin.
    """
    return {
        "total_users": db.query(func.count(models.User.user_id)).scalar(),
        "total_strategies": db.query(func.count(models.Strategy.strategy_id)).scalar(),
        "total_backtests": db.query(func.count(models.BacktestJob.job_id)).scalar(),
        "pending_jobs": db.query(func.count(models.BacktestJob.job_id))
            .filter(models.BacktestJob.status == models.JobStatus.pending).scalar(),
        "total_trades_logged": db.query(func.count(models.TradeLog.log_id)).scalar(),
    }

@app.put("/admin/users/{user_id}/promote", response_model=schemas.UserAdminOut)
def promote_user_to_admin(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin_user: models.User = Depends(get_current_admin)
):
    """
    Promotes a normal user to Admin.
    """
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role == models.UserRole.admin:
        raise HTTPException(status_code=400, detail="User is already an admin")

    user.role = models.UserRole.admin
    db.commit()
    db.refresh(user)
    
    # Return schema requires strategy_count, calculate it or set 0
    return schemas.UserAdminOut(
        user_id=user.user_id,
        username=user.username,
        created_at=user.created_at,
        role=user.role.value,
        strategy_count=len(user.strategies) # SQLAlchemy relationship makes this easy
    )