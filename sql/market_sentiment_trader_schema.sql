CREATE DATABASE market_sentiment_trader;	

-- ==========================================
-- GROUP A: REFERENCE & PUBLIC DATA
-- ==========================================

-- 1. STOCKS (The Center of the Database)
CREATE TABLE stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100)
);

-- 2. STOCK_PRICES (Public Data)
CREATE TABLE stock_prices (
    price_id INT AUTO_INCREMENT PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open_price DECIMAL(14, 2),
    close_price DECIMAL(14, 2),
    volume BIGINT,
    FOREIGN KEY (ticker) REFERENCES stocks(ticker),
    UNIQUE KEY (ticker, date) -- Ensures only one price record per stock per day
);

-- 3. NEWS_ARTICLES (Raw Text)
CREATE TABLE news_articles (
    article_id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    headline VARCHAR(500) NOT NULL,
    source VARCHAR(100),
    url VARCHAR(500)
);

-- 4. REDDIT_POSTS (Raw Text)
CREATE TABLE reddit_posts (
    post_id VARCHAR(20) PRIMARY KEY, -- Reddit IDs are strings
    date DATE NOT NULL,
    title VARCHAR(500) NOT NULL,
    body TEXT,
    score INT,
    comment_count INT
);

-- ==========================================
-- GROUP B: DERIVED SENTIMENT (The "Bridge" Tables)
-- ==========================================

-- 5. NEWS_SENTIMENT_MENTIONS
CREATE TABLE news_sentiment_mentions (
    mention_id INT AUTO_INCREMENT PRIMARY KEY,
    article_id INT NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment_label ENUM('positive', 'neutral', 'negative'),
    confidence_score DECIMAL(5, 4),
    
    FOREIGN KEY (article_id) REFERENCES news_articles(article_id) ON DELETE CASCADE,
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    UNIQUE KEY (article_id, ticker)
);

-- 6. REDDIT_SENTIMENT_MENTIONS
CREATE TABLE reddit_sentiment_mentions (
    mention_id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(20) NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    sentiment_label ENUM('positive', 'neutral', 'negative'),
    confidence_score DECIMAL(5, 4),
    
    FOREIGN KEY (post_id) REFERENCES reddit_posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE CASCADE,
    UNIQUE KEY (post_id, ticker)
);

-- ==========================================
-- GROUP C: APPLICATION LOGIC (Users & Back-testing)
-- ==========================================

-- 7. USERS
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. STRATEGIES
CREATE TABLE strategies (
    strategy_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    buy_rules_json JSON,
    sell_rules_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 9. BACKTEST_JOBS (The Queue)
CREATE TABLE backtest_jobs (
    job_id INT AUTO_INCREMENT PRIMARY KEY,
    strategy_id INT NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
);

-- 10. BACKTEST_RESULTS (Summary Stats)
CREATE TABLE backtest_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    job_id INT NOT NULL,
    total_return_pct DECIMAL(10, 2),
    win_rate DECIMAL(5, 2),
    max_drawdown_pct DECIMAL(10, 2),
    FOREIGN KEY (job_id) REFERENCES backtest_jobs(job_id)
);

-- 11. TRADE_LOGS (Detailed History)
CREATE TABLE trade_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    result_id INT NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    action ENUM('BUY', 'SELL') NOT NULL,
    date DATE NOT NULL,
    price DECIMAL(14, 2) NOT NULL,
    quantity INT NOT NULL,
    profit DECIMAL(14, 2),
    
    FOREIGN KEY (result_id) REFERENCES backtest_results(result_id),
    FOREIGN KEY (ticker) REFERENCES stocks(ticker) -- Validates the stock exists
);