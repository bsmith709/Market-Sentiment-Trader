from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db, engine
import models

# This line creates tables if they don't exist (good for dev)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "healthy", "project": "Sentiment Backtester"}

@app.get("/stocks")
def read_stocks(db: Session = Depends(get_db)):
    stocks = db.query(models.Stock).all()
    return stocks