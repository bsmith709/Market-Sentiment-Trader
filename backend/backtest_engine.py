from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import models
from database import SessionLocal
from celery_app import celery
import traceback 

# --- CONFIG ---
INITIAL_CASH = 100000.00

@celery.task(name="run_backtest_task")
def run_backtest(job_id: int):
    """
    Production-Grade Backtest Engine.
    Features: 
        - Event-Driven (Splits/Dividends)
        - Risk Managed (Stop Loss, Take Profit, Trailing Stop)
        - Signal Filtered (SMA, EMA, Cooldown)
    """
    db = SessionLocal()
    try:
        print(f"--- Starting Backtest Job {job_id} ---")
        
        # Load Context
        job = db.query(models.BacktestJob).get(job_id)
        strategy = job.strategy
        
        if not strategy.rules:
            print("No rules found.")
            job.status = models.JobStatus.failed
            db.commit()
            return

        # Extract tickers for batch querying
        # strategy.rules is a List of Dicts (JSONB)
        tickers = [r['ticker'] for r in strategy.rules]

        # ---------------------------------------------------
        # BATCH DATA LOADING
        # ---------------------------------------------------
        print("Pre-loading market data...")
        
        # A. Prices
        # Map: price_map[date][ticker] = { close, volume }
        price_rows = db.query(models.StockPrice).filter(
            models.StockPrice.ticker.in_(tickers)
        ).order_by(models.StockPrice.date.asc()).all()
        
        price_map = {}
        for p in price_rows:
            if p.date not in price_map: price_map[p.date] = {}
            price_map[p.date][p.ticker] = p

        # B. Sentiment Scores
        # Map: score_map[date][ticker] = { news, reddit }
        score_rows = db.query(models.DailySentimentScore).filter(
            models.DailySentimentScore.ticker.in_(tickers)
        ).all()
        
        score_map = {}
        for s in score_rows:
            if s.date not in score_map: score_map[s.date] = {}
            score_map[s.date][s.ticker] = s

        # C. Corporate Actions (Splits & Dividends)
        # Map: event_map[date][ticker] = { type: 'split'/'div', value: ... }
        div_rows = db.query(models.Dividend).filter(models.Dividend.ticker.in_(tickers)).all()
        split_rows = db.query(models.StockSplit).filter(models.StockSplit.ticker.in_(tickers)).all()
        
        event_map = {}
        for d in div_rows:
            if d.ex_date not in event_map: event_map[d.ex_date] = {}
            event_map[d.ex_date][d.ticker] = {'type': 'div', 'amount': float(d.amount)}
        
        for s in split_rows:
            if s.date not in event_map: event_map[s.date] = {}
            event_map[s.date][s.ticker] = {'type': 'split', 'ratio': float(s.ratio)}

        # D. Define Simulation Timeline
        # Sorted unique dates
        sim_dates = sorted(price_map.keys())

        # ---------------------------------------------------
        # INITIALIZE STATE
        # ---------------------------------------------------
        cash = INITIAL_CASH
        holdings = {t: 0 for t in tickers} # { "AAPL": 0 }
        trades = []

        # Stats tracking
        peak_value = INITIAL_CASH
        max_drawdown = 0.0
        winning_trades = 0
        total_sell_trades = 0

        # State tracking
        cost_basis = {t: 0.0 for t in tickers} # Average price per share
        last_sell_date = {t: None for t in tickers}  # For Cooldown
        highest_price_seen = {t: 0.0 for t in tickers} # For Trailing Stop
        
        # Indicators
        price_history = {t: [] for t in tickers}     # List of Close prices for SMA
        hype_ema_state = {t: {'news': 0.5, 'reddit': 0.5} for t in tickers} # Current EMA
        prev_day_scores = {t: {'news': 0.5, 'reddit': 0.5} for t in tickers} # For Momentum Delta
        
        # ---------------------------------------------------
        # THE TIME LOOP
        # ---------------------------------------------------
        print(f"Simulating {len(sim_dates)} days...")
        
        for current_date in sim_dates:
            
            # --- PHASE A: CORPORATE ACTIONS (Morning) ---
            if current_date in event_map:
                for ticker, event in event_map[current_date].items():
                    qty = holdings.get(ticker, 0)
                    if qty > 0:
                        if event['type'] == 'div':
                            payout = qty * event['amount']
                            cash += payout
                            
                        elif event['type'] == 'split':
                            # 2:1 split means ratio 2.0. We multiply shares.
                            new_qty = int(qty * event['ratio'])
                            holdings[ticker] = new_qty
                            # Adjust cost basis (split reduces cost per share)
                            cost_basis[ticker] = cost_basis[ticker] / event['ratio']
                            # If stock splits 2:1, price drops 50%. 
                            # We must drop the "Peak" 50% too, or Trailing Stop fires instantly.
                            highest_price_seen[ticker] = highest_price_seen[ticker] / event['ratio']

            # --- PHASE B: TRADING (Market Close) ---
            
            # Calculate Portfolio Value (Cash + Current Stock Value)
            # Needed for Position Sizing
            daily_prices = price_map[current_date]

            # Update Price History for SMA
            for t, p_data in daily_prices.items():
                price_history[t].append(float(p_data.close_price))

            # Portfolio Value and Drawdown
            portfolio_value = cash
            for t, qty in holdings.items():
                if t in daily_prices and qty > 0:
                    portfolio_value += (qty * float(daily_prices[t].close_price))

            if portfolio_value > peak_value:
                peak_value = portfolio_value
            
            drawdown = (portfolio_value - peak_value) / peak_value
            if drawdown < max_drawdown: # Drawdown is negative, so lower is worse
                max_drawdown = drawdown
            
            # Iterate RULES in ORDER (User Priority)
            for rule in strategy.rules:
                ticker = rule['ticker']

                # Check Data Availability
                if ticker not in daily_prices: continue

                # --- CALCULATE INDICATORS ---
                # OHLC Data
                p_data = daily_prices[ticker]
                open_p = float(p_data.open_price)
                high_p = float(p_data.high_price)
                low_p = float(p_data.low_price)
                close_p = float(p_data.close_price)

                # Hype Smoothing (EMA)
                raw_scores = score_map.get(current_date, {}).get(ticker)
                raw_n = float(raw_scores.news_score) if raw_scores and raw_scores.news_score is not None else 0.5
                raw_r = float(raw_scores.reddit_score) if raw_scores and raw_scores.reddit_score is not None else 0.5
                daily_mentions = raw_scores.mention_count if raw_scores else 0

                window = rule.get('hype_smoothing_window', 0)
                if window > 0:
                    k = 2 / (window + 1)
                    n_score = (raw_n * k) + (hype_ema_state[ticker]['news'] * (1 - k))
                    r_score = (raw_r * k) + (hype_ema_state[ticker]['reddit'] * (1 - k))
                    hype_ema_state[ticker] = {'news': n_score, 'reddit': r_score}
                else:
                    n_score = raw_n
                    r_score = raw_r

                # Sentiment Momentum (Delta)
                n_delta = n_score - prev_day_scores[ticker]['news']
                r_delta = r_score - prev_day_scores[ticker]['reddit']
                prev_day_scores[ticker] = {'news': n_score, 'reddit': r_score}

                # Price SMA
                sma_days = rule.get('price_sma_days')
                current_sma = None
                if sma_days and len(price_history[ticker]) >= sma_days:
                    window_slice = price_history[ticker][-sma_days:]
                    current_sma = sum(window_slice) / sma_days

                # --- EXIT RULES (RISK MANAGEMENT) ---
                # Check these BEFORE sentiment rules. Risk trumps Opportunity.
                if holdings[ticker] > 0:
                    # Update Peak for Trailing Stop
                    if high_p > highest_price_seen[ticker]:
                        highest_price_seen[ticker] = high_p
                    
                    avg_cost = cost_basis[ticker]
                    
                    # Calculate potential exits
                    should_sell_risk = False
                    sell_reason = ""
                    execution_price = close_p # Default exit at close

                    # Stop Loss (Intraday Check using Low)
                    sl = rule.get('stop_loss_pct')
                    if sl:
                        stop_price = avg_cost * (1.0 - sl)
                        if low_p <= stop_price:
                            should_sell_risk = True
                            sell_reason = "Stop Loss"
                            # Simulate getting stopped out. Conservative estimate: 
                            # If it gapped down below stop, we sell at Open. 
                            # Otherwise we sell at Stop Price.
                            execution_price = min(open_p, stop_price)

                    # Take Profit (Intraday Check using High)
                    tp = rule.get('take_profit_pct')
                    if tp and not should_sell_risk:
                        target_price = avg_cost * (1.0 + tp)
                        if high_p >= target_price:
                            should_sell_risk = True
                            sell_reason = "Take Profit"
                            execution_price = target_price

                    # Trailing Stop (Intraday Check using High/Low)
                    ts = rule.get('trailing_stop_pct')
                    if ts and not should_sell_risk:
                        trail_price = highest_price_seen[ticker] * (1.0 - ts)
                        if low_p <= trail_price:
                            should_sell_risk = True
                            sell_reason = "Trailing Stop"
                            execution_price = min(open_p, trail_price)

                    if should_sell_risk:
                        # EXECUTE RISK SELL
                        qty = holdings[ticker]
                        revenue = qty * execution_price
                        profit = revenue - (qty * avg_cost)
                        
                        total_sell_trades += 1
                        if profit > 0: winning_trades += 1

                        cash += revenue
                        holdings[ticker] = 0
                        cost_basis[ticker] = 0.0
                        highest_price_seen[ticker] = 0.0
                        last_sell_date[ticker] = current_date # Mark cooldown trigger
                        
                        trades.append({
                            "date": current_date, "action": models.TradeAction.SELL, "ticker": ticker,
                            "price": execution_price, "quantity": qty, "profit": profit
                        })
                        continue # Done with ticker for today

                # --- ENTRY / SIGNAL RULES ---

                # Check Logic (Momentum vs Reversion)
                rule_type = rule.get('type', 'momentum')

                def is_buy_signal(score, threshold):
                    if threshold is None: return False
                    return score >= threshold if rule_type == 'momentum' else score <= threshold

                def is_sell_signal(score, threshold):
                    if threshold is None: return False
                    return score <= threshold if rule_type == 'momentum' else score >= threshold
                
                # --- FILTERS (Must Pass All) ---
                
                # Filter 1: Cooldown
                cooldown = rule.get('cooldown_days', 0)
                if last_sell_date[ticker]:
                    days_since = (current_date - last_sell_date[ticker]).days
                    if days_since < cooldown:
                        continue 

                # Filter 2: Min Mentions
                if daily_mentions < rule.get('min_mentions', 0):
                    continue

                # Filter 3: SMA Trend
                # Buy only if Price > SMA (Bullish Trend)
                if current_sma and close_p < current_sma:
                    continue

                # Filter 4: Sentiment Momentum
                n_mom_min = rule.get('news_hype_delta_min')
                if n_mom_min and abs(n_delta) < n_mom_min: continue

                r_mom_min = rule.get('reddit_hype_delta_min')
                if r_mom_min and abs(r_delta) < r_mom_min: continue
                
                # --- SIGNALS ---
                n_sell = is_sell_signal(n_score, rule.get('news_sell_threshold'))
                r_sell = is_sell_signal(r_score, rule.get('reddit_sell_threshold'))
                should_sell_signal = (n_sell or r_sell)
                
                if should_sell_signal and holdings[ticker] > 0:
                    # EXECUTE SELL
                    qty = holdings[ticker]
                    revenue = qty * close_p

                    # Calculate Profit
                    avg_cost = cost_basis[ticker]
                    total_cost = qty * avg_cost
                    profit = revenue - total_cost
                    
                    # Update Stats
                    total_sell_trades += 1
                    if profit > 0:
                        winning_trades += 1

                    cash += revenue
                    holdings[ticker] = 0
                    cost_basis[ticker] = 0.0 # Reset cost basis
                    highest_price_seen[ticker] = 0.0
                    last_sell_date[ticker] = current_date # Triggers cooldown
                    
                    trades.append({
                        "date": current_date, "action": models.TradeAction.SELL, "ticker": ticker,
                        "price": close_p, "quantity": qty, "profit": profit
                    })
                    continue # Done with this ticker

                # SIGNAL BUY
                n_buy = is_buy_signal(n_score, rule.get('news_buy_threshold'))
                r_buy = is_buy_signal(r_score, rule.get('reddit_buy_threshold'))
                should_buy = (n_buy or r_buy)
                
                if should_buy:
                    # RISK MANAGEMENT: Position Sizing
                    
                    # Get Limit: "Max 20% in AAPL"
                    # (Use .get with default 0.2 if column missing in old strategies)
                    max_pct = float(rule.get('max_allocation_pct', 0.2))
                    
                    target_position_value = portfolio_value * max_pct
                    current_position_value = holdings[ticker] * close_p
                    
                    # Calculate Room: "Can I buy more?"
                    room_to_buy = target_position_value - current_position_value
                    
                    if room_to_buy > 0 and cash > close_p:
                        # Calculate Quantity
                        # Constrained by Risk Limit AND Available Cash
                        qty_limit = int(room_to_buy / close_p)
                        cash_limit = int(cash / close_p)
                        
                        buy_qty = min(qty_limit, cash_limit)
                        
                        if buy_qty > 0:
                            # EXECUTE BUY
                            cost = buy_qty * close_p

                            # Weighted Average Cost Basis
                            old_qty = holdings[ticker]
                            old_total_cost = old_qty * cost_basis[ticker]
                            new_total_cost = old_total_cost + cost
                            new_qty = old_qty + buy_qty
                            cost_basis[ticker] = new_total_cost / new_qty # Update average cost

                            # Initialize Peak for Trailing Stop
                            if close_p > highest_price_seen[ticker]:
                                highest_price_seen[ticker] = close_p

                            cash -= cost
                            holdings[ticker] += buy_qty
                            
                            trades.append({
                                "date": current_date, "action": models.TradeAction.BUY, "ticker": ticker,
                                "price": close_p, "quantity": buy_qty, "profit": None
                            })

        # ---------------------------------------------------
        # SAVE RESULTS
        # ---------------------------------------------------
        print("Saving results...")
        
        # Calculate Final Stats
        final_value = cash
        # Add value of remaining holdings
        # Use the price from the LAST day of simulation
        last_date = sim_dates[-1]
        if last_date in price_map:
            for t, qty in holdings.items():
                if qty > 0 and t in price_map[last_date]:
                    final_value += (qty * float(price_map[last_date][t].close_price))
        
        total_return = ((final_value - INITIAL_CASH) / INITIAL_CASH) * 100
        win_rate_pct = 0.0
        if total_sell_trades > 0:
            win_rate_pct = (winning_trades / total_sell_trades) * 100
        max_drawdown_pct = max_drawdown * 100
        
        # Create Result Record
        result = models.BacktestResult(
            job_id=job.job_id,
            total_return_pct=total_return,
            win_rate=win_rate_pct,
            max_drawdown_pct=max_drawdown_pct
        )
        db.add(result)
        db.commit() # Get result ID
        db.refresh(result)
        
        # Save Trade Logs
        log_objects = []
        for t in trades:
            log_objects.append(models.TradeLog(
                result_id=result.result_id,
                ticker=t['ticker'],
                action=t['action'],
                date=t['date'],
                price=t['price'],
                quantity=t['quantity'],
                profit=t['profit']
            ))
        
        if log_objects:
            db.add_all(log_objects)
            
        # GAMIFICATION: Update Leaderboard
        # Only add positive returns to the high score table
        if total_return > 0:
            # Check if entry exists for this backtest (idempotency)
            existing = db.query(models.LeaderboardEntry).filter(
                models.LeaderboardEntry.backtest_id == result.result_id
            ).first()
            
            if not existing:
                entry = models.LeaderboardEntry(
                    user_id=strategy.user_id,
                    strategy_id=strategy.strategy_id,
                    backtest_id=result.result_id,
                    total_return_pct=total_return,
                    rank_date=datetime.utcnow().date()
                )
                db.add(entry)

        job.status = models.JobStatus.completed
        job.completed_at = datetime.utcnow()

        db.commit()
        print(f"Job {job_id} Finished. Return: {total_return:.2f}%")

    except Exception as e:
        print(f"CRASH in Backtest Job {job_id}: {e}")
        traceback.print_exc() # Print full error stack trace to console
        
        # Attempt to mark job as failed
        try:
            job = db.query(models.BacktestJob).get(job_id)
            if job:
                job.status = models.JobStatus.failed
                db.commit()
        except:
            pass # DB connection might be broken
    finally:
        db.close()