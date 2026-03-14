from fastapi import APIRouter
import yfinance as yf
from pydantic import BaseModel
import os
import pandas as pd


router = APIRouter()

@router.get("/")
async def list_trades():
    data = yf.download("AAPL", start="2010-01-01")
    data.columns = data.columns.droplevel(1)
    data = data.reset_index()
    result = data.to_dict(orient="records")
    return result 

def getMovingAvg(data, duration):
    if duration >= len(data):
        return
    print(len(data[:duration]))
    movingSum = sum(item["Close"] for item in data[:duration])
    for i in range(duration, len(data)):
        data[i][f"moving{duration}"] = (movingSum/duration)
        movingSum -= data[i-duration]["Close"]
        movingSum += data[i]["Close"]
    return

# def getRSI(data, duration=14):
#     avg = 0
#     sofarLoss = 0
#     sofarGain = 0
#     data[0]["GainLoss"] = 0
#     for i in range(1,len(data)):
#         data[i]["GainLoss"] = data[i]["Close"] - data[i-1]["Close"]
#         if data[i]["Close"] > data[i-1]["Close"]:
#             sofarGain += data[i]["Close"] - data[i-1]["Close"]
#         else:
#             sofarLoss += data[i-1]["Close"] - data[i]["Close"]
#         if i >= duration:
#             if data[i-duration]["GainLoss"] > 0:
#                 sofarGain -= data[i-duration]["GainLoss"]
#             else:
#                 sofarLoss -= data[i-duration]["GainLoss"]
#             data[i]["RSI"] = 100 - (100/(1+((sofarGain/duration)/(sofarLoss/duration))))
#             print(data[i]["RSI"] )
#     return
        
def getRSI(data, duration=14):
    sofarLoss = 0
    sofarGain = 0
    rsi_values = []

    data[0]["GainLoss"] = 0

    for i in range(1, len(data)):
        change = data[i]["Close"] - data[i-1]["Close"]
        data[i]["GainLoss"] = change

        gain = max(change, 0)
        loss = max(-change, 0)

        sofarGain += gain
        sofarLoss += loss

        if i > duration:
            oldest_change = data[i-duration]["GainLoss"]

            if oldest_change > 0:
                sofarGain -= oldest_change
            else:
                sofarLoss -= abs(oldest_change)

        if i >= duration:
            avg_gain = sofarGain / duration
            avg_loss = sofarLoss / duration

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            data[i]["RSI"] = rsi
            rsi_values.append(rsi)

    return rsi_values

            


@router.get("/trades/{ticker}")
async def get_stock(
    ticker: str,
    start: str = "2010-01-01",
    end: str = "2025-01-01",
):
    ticker = ticker.upper()
    os.makedirs("data", exist_ok=True)
    file_path = f"data/{ticker}.csv"

    if os.path.exists(file_path):
        print("data in file")
        data = pd.read_csv(file_path)
    else:
        print("downloading data...")
        data = yf.download(ticker, start=start, end=end)
        print("download finished")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        data = data.reset_index()
        data.to_csv(file_path, index=False)
    result = data.where(pd.notnull(data), None).to_dict(orient="records")
    getMovingAvg(result, 5)
    getMovingAvg(result, 10)
    getMovingAvg(result, 20)
    getRSI(result, 10)
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