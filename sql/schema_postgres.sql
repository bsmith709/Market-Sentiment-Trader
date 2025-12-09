-- PostgreSQL Schema

-- 1. STOCKS
CREATE TABLE stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100)
);

-- 2. STOCK_PRICES
CREATE TABLE stock_prices (
    price_id SERIAL PRIMARY KEY, -- 'SERIAL' handles auto-increment
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    date DATE NOT NULL,
    open_price NUMERIC(14, 2), -- 'NUMERIC' is more precise than DECIMAL in Postgres
    close_price NUMERIC(14, 2),
    high_price NUMERIC(14, 2),
    low_price NUMERIC(14, 2),
    volume BIGINT,
    UNIQUE (ticker, date)
);

-- 3. NEWS_ARTICLES
CREATE TABLE news_articles (
    article_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    headline TEXT NOT NULL, -- Postgres prefers TEXT over VARCHAR for long strings
    source VARCHAR(100),
    url TEXT
);

-- 4. REDDIT_POSTS
CREATE TABLE reddit_posts (
    post_id VARCHAR(20) PRIMARY KEY,
    date DATE NOT NULL,
    title TEXT NOT NULL,
    body TEXT,
    score INT,
    comment_count INT
);

-- ENUM Type (Postgres requires creating it first)
CREATE TYPE sentiment_type AS ENUM ('positive', 'neutral', 'negative');

-- 5. NEWS_SENTIMENT_MENTIONS
CREATE TABLE news_sentiment_mentions (
    mention_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    article_id INT NOT NULL REFERENCES news_articles(article_id) ON DELETE CASCADE,
    sentiment_label sentiment_type, -- Uses the ENUM we created above
    confidence_score NUMERIC(5, 4),
    UNIQUE (article_id, ticker)
);

-- 6. REDDIT_SENTIMENT_MENTIONS
CREATE TABLE reddit_sentiment_mentions (
    mention_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker) ON DELETE CASCADE,
    post_id VARCHAR(20) NOT NULL REFERENCES reddit_posts(post_id) ON DELETE CASCADE,
    sentiment_label sentiment_type,
    confidence_score NUMERIC(5, 4),
    UNIQUE (post_id, ticker)
);

-- ENUM Type for User Roles
CREATE TYPE user_role AS ENUM ('user', 'admin');

-- 7. USERS
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. STRATEGIES
CREATE TABLE strategies (
    strategy_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job Status Enum
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed');

-- 9. BACKTEST_JOBS
CREATE TABLE backtest_jobs (
    job_id SERIAL PRIMARY KEY,
    strategy_id INT NOT NULL REFERENCES strategies(strategy_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status job_status DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- 10. BACKTEST_RESULTS
CREATE TABLE backtest_results (
    result_id SERIAL PRIMARY KEY,
    job_id INT NOT NULL REFERENCES backtest_jobs(job_id),
    total_return_pct NUMERIC(10, 2),
    win_rate NUMERIC(5, 2),
    max_drawdown_pct NUMERIC(10, 2)
);

-- Trade Action Enum
CREATE TYPE trade_action AS ENUM ('BUY', 'SELL');

-- 11. TRADE_LOGS
CREATE TABLE trade_logs (
    log_id SERIAL PRIMARY KEY,
    result_id INT NOT NULL REFERENCES backtest_results(result_id),
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    action trade_action NOT NULL,
    date DATE NOT NULL,
    price NUMERIC(14, 2) NOT NULL,
    quantity INT NOT NULL,
    profit NUMERIC(14, 2) -- Nullable for BUYs
);

-- 12. DAILY_SENTIMENT_AGGREGATES
-- Caches the calculated score so Backtester doesn't have to scan raw posts
CREATE TABLE daily_sentiment_aggregates (
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    date DATE NOT NULL,
    news_score NUMERIC(5, 4),   -- 0.0000 to 1.0000
    reddit_score NUMERIC(5, 4), -- 0.0000 to 1.0000
    mention_count INT DEFAULT 0,
    PRIMARY KEY (ticker, date)
);

-- 13. MARKET_HOLIDAYS
-- Prevents the engine from trying to fetch data on closed days
CREATE TABLE market_holidays (
    date DATE PRIMARY KEY,
    name VARCHAR(100) -- e.g., "Christmas Day"
);

-- 14. DIVIDENDS
-- Essential for calculating Total Return (Price + Payouts)
CREATE TABLE dividends (
    dividend_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    ex_date DATE NOT NULL,
    amount NUMERIC(10, 4) NOT NULL, -- Cash amount per share
    UNIQUE (ticker, ex_date)
);

-- 15. STOCK_SPLITS
-- Essential for normalizing historical price data
CREATE TABLE stock_splits (
    split_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL REFERENCES stocks(ticker),
    date DATE NOT NULL,
    ratio NUMERIC(10, 4) NOT NULL, -- e.g., 0.5 for 2-for-1 split
    UNIQUE (ticker, date)
);

-- 16. LEADERBOARD
-- High Scores for the entire platform
CREATE TABLE leaderboard (
    entry_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    strategy_id INT NOT NULL REFERENCES strategies(strategy_id) ON DELETE CASCADE,
    backtest_id INT NOT NULL REFERENCES backtest_results(result_id),
    
    total_return_pct NUMERIC(10, 2) NOT NULL,
    rank_date DATE DEFAULT CURRENT_DATE,
    
    -- Constraint: A backtest can only appear once per day
    UNIQUE (backtest_id, rank_date)
);