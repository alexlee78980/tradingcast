from fastapi import APIRouter, Query
import yfinance as yf
from pydantic import BaseModel
import os
import pandas as pd
from .models import analyze, compare, get_tickers, get_stock_data
import asyncio
from functools import partial


router = APIRouter()

@router.get("/")
async def list_trades():
    data = yf.download("AAPL", start="2010-01-01")
    data.columns = data.columns.droplevel(1)
    data = data.reset_index()
    result = data.to_dict(orient="records")
    return result 
            


@router.get("/v1/get/{ticker}")
async def get_stock(
    ticker: str,
    start: str = "2010-01-01",
    end: str = "2025-01-01",
):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, partial(get_stock_data, ticker, start, end))
    return result


class StockDownloadProp(BaseModel):
    ticker:str
    start:str
    end: str = None
@router.post("/download")
async def download_stock(req: StockDownloadProp):
    if req.end:
        data = yf.download(req.ticker, start=req.start, end=req.end)
    else:
        data = yf.download(req.ticker, start=req.start)
    os.makedirs("data", exist_ok=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    data = data.reset_index()
    file_path = f"data/{req.ticker}.csv"
    data.to_csv(file_path, index=False)

    return {
        "message": "downloaded",
        "file": file_path
    }


            

class StockDownloadProp(BaseModel):
    ticker:str
    start:str
    end: str = None
@router.post("/download")
async def download_stock(req: StockDownloadProp):
    print("called download")
    if req.end:
        data = yf.download(req.ticker, start=req.start, end=req.end)
    else:
        data = yf.download(req.ticker, start=req.start)
    os.makedirs("data", exist_ok=True)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.droplevel(1)
    data = data.reset_index()
    file_path = f"data/{req.ticker}.csv"
    data.to_csv(file_path, index=False)

    return {
        "message": "downloaded",
        "file": file_path
    }

@router.get("/v1/analyze/{ticker}")
async def analyze_route(ticker: str, tickers: str = Query(...)):
    ticker_list = tickers.split(',')
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, partial(analyze, ticker, ticker_list))
    print("call finished")
    return result


@router.get("/v1/tickers")
async def tickers_list():
    return get_tickers()


@router.get("/v1/getCorrelation/{ticker}")
async def get_correlation(ticker: str, tickers: str = Query(default=None)):
    print(tickers)
    ticker_list = []
    if not tickers:
        ticker_list = get_tickers()
    else:
        ticker_list = [t.strip() for t in tickers.split(',') if t.strip()]
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, partial(compare, ticker, ticker_list))
    return result