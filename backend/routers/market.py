from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd
from tradingview_ta import TA_Handler, Interval

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
    Fetch technical analysis signals (Strong Buy, Buy, Sell, etc.) from TradingView
    across multiple timeframes.
    """
    try:
        tv_symbol = symbol.replace(".IS", "")
        
        intervals = {
            "15 Dakika": Interval.INTERVAL_15_MINUTES,
            "1 Saat": Interval.INTERVAL_1_HOUR,
            "4 Saat": Interval.INTERVAL_4_HOURS,
            "Günlük": Interval.INTERVAL_1_DAY,
            "Haftalık": Interval.INTERVAL_1_WEEK,
            "Aylık": Interval.INTERVAL_1_MONTH,
        }
        
        results = {}
        for label, interval in intervals.items():
            try:
                handler = TA_Handler(
                    symbol=tv_symbol,
                    screener="turkey",
                    exchange="BIST",
                    interval=interval
                )
                analysis = handler.get_analysis()
                results[label] = {
                    "summary": analysis.summary,
                    "oscillators": analysis.oscillators,
                    "moving_averages": analysis.moving_averages
                }
            except Exception as e:
                # If a specific timeframe fails, skip or set as error
                results[label] = {"error": str(e)}

        return {
            "symbol": symbol,
            "timeframes": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch TV signals: {str(e)}")

@router.get("/chart/{symbol}")
def get_chart_data(symbol: str, interval: str = "1d"):
    """
    Fetch OHLCV data for charts, along with EMA and Volume MA indicators.
    """
    try:
        yf_symbol = symbol if symbol.endswith(".IS") else f"{symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        
        # Define period based on interval
        period = "1y" if interval in ["1d", "1wk", "1mo"] else "60d"
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No chart data available")
            
        # Calculate EMA (e.g., 20 period EMA)
        hist['EMA'] = hist['Close'].ewm(span=20, adjust=False).mean()
        
        # Calculate Volume MA (e.g., 20 period moving average of volume)
        hist['VolumeMA'] = hist['Volume'].rolling(window=20).mean()
        
        # Handle NaN values by replacing them with None or 0 for JSON serialization
        hist = hist.fillna(0)
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                "time": index.timestamp() * 1000, # milliseconds
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume']),
                "ema": round(row['EMA'], 2) if row['EMA'] > 0 else None,
                "volume_ma": int(row['VolumeMA']) if row['VolumeMA'] > 0 else None
            })
            
        return {"symbol": symbol, "interval": interval, "data": data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chart data: {str(e)}")

