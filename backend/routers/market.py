from fastapi import APIRouter, HTTPException
import yfinance as yf
from tradingview_ta import TA_Handler, Interval, Exchange
import requests
from bs4 import BeautifulSoup

router = APIRouter()

@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """
    Fetch the latest quote and daily change for a symbol using yfinance.
    For BIST, symbols usually end with .IS (e.g. THYAO.IS).
    """
    try:
        # Ensure BIST symbols have .IS suffix
        yf_symbol = symbol if symbol.endswith(".IS") else f"{symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        
        # Get today's data
        hist = ticker.history(period="2d")
        if hist.empty or len(hist) < 1:
            raise HTTPException(status_code=404, detail="Symbol not found or no data available")
            
        current_price = hist['Close'].iloc[-1]
        
        if len(hist) >= 2:
            prev_close = hist['Close'].iloc[-2]
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
        else:
            change = 0
            change_percent = 0

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}")
def get_signals(symbol: str):
    """
    Fetch technical analysis signals (Strong Buy, Buy, Sell, etc.) from TradingView.
    """
    try:
        tv_symbol = symbol.replace(".IS", "")
        handler = TA_Handler(
            symbol=tv_symbol,
            screener="turkey",
            exchange="BIST",
            interval=Interval.INTERVAL_1_DAY
        )
        analysis = handler.get_analysis()
        return {
            "symbol": symbol,
            "summary": analysis.summary,
            "oscillators": analysis.oscillators,
            "moving_averages": analysis.moving_averages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch TV signals: {str(e)}")

