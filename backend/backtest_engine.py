from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import models
from database import SessionLocal
import traceback 

# --- CONFIG ---
INITIAL_CASH = 10000.00

def run_backtest(job_id: int):
    """
    Production-Grade Backtest Engine.
    Features: Event-Driven, Split/Dividend aware, Risk Managed.
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

        cost_basis = {t: 0.0 for t in tickers} # Average price per share

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
        peak_value = INITIAL_CASH
        max_drawdown = 0.0
        winning_trades = 0
        total_sell_trades = 0
        
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

            # --- PHASE B: TRADING (Market Close) ---
            
            # Calculate Portfolio Value (Cash + Current Stock Value)
            # Needed for Position Sizing
            daily_prices = price_map[current_date]
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

                # Get Settings specific to this stock
                rule_type = rule.get('type', 'momentum') # Default to momentum

                # Helper Logic based on THIS rule's type
                def is_buy_signal(score, threshold):
                    if threshold is None: return False
                    if rule_type == 'momentum':
                        return score >= threshold
                    else: # reversion
                        return score <= threshold

                def is_sell_signal(score, threshold):
                    if threshold is None: return False
                    if rule_type == 'momentum':
                        return score <= threshold
                    else: # reversion
                        return score >= threshold
                
                # Check Data Availability
                if ticker not in daily_prices: continue
                price_data = daily_prices[ticker]
                close_p = float(price_data.close_price)
                
                # Get Scores (Default to 0.5 if missing)
                scores = score_map.get(current_date, {}).get(ticker)
                n_score = float(scores.news_score) if scores and scores.news_score is not None else 0.5
                r_score = float(scores.reddit_score) if scores and scores.reddit_score is not None else 0.5

                # Check Logic Signals
                
                # --- SELL LOGIC (Priority) ---
                # Check News Sell
                ns_thresh = rule.get('news_sell_threshold')
                news_sell = is_sell_signal(n_score, ns_thresh)
                
                # Check Reddit Sell
                rs_thresh = rule.get('reddit_sell_threshold')
                reddit_sell = is_sell_signal(r_score, rs_thresh)
                
                if (news_sell or reddit_sell) and holdings[ticker] > 0:
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
                    
                    trades.append({
                        "date": current_date, "action": models.TradeAction.SELL, "ticker": ticker,
                        "price": close_p, "quantity": qty, "profit": profit
                    })
                    continue # Done with this ticker

                # --- BUY LOGIC ---
                # Only buy if NOT selling
                
                # Check News Buy
                nb_thresh = rule.get('news_buy_threshold')
                news_buy = is_buy_signal(n_score, nb_thresh)
                
                # Check Reddit Buy
                rb_thresh = rule.get('reddit_buy_threshold')
                reddit_buy = is_buy_signal(r_score, rb_thresh)
                
                # ENTRY: If ANY signal says buy (and the other isn't vetoing via logic above)
                should_buy = (news_buy or reddit_buy)
                
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