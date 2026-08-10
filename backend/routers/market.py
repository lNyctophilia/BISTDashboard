from fastapi import APIRouter, HTTPException
import yfinance as yf
import pandas as pd
from tradingview_ta import TA_Handler, Interval
import time
import random
import tradingview_ta.main

# Monkey patch tradingview_ta to use a standard browser User-Agent to prevent 429 errors
original_tv_post = tradingview_ta.main.requests.post
def patched_tv_post(url, **kwargs):
    if "headers" in kwargs:
        kwargs["headers"]["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    return original_tv_post(url, **kwargs)
tradingview_ta.main.requests.post = patched_tv_post

router = APIRouter()

def _clean_symbol(symbol: str) -> str:
    s = symbol.upper().strip()
    if s.startswith("BIST:"):
        s = s.replace("BIST:", "", 1)
    if s.endswith(".IS"):
        s = s.replace(".IS", "")
    return s

BIST_COMPANY_NAMES = {
    "THYAO": "Türk Hava Yolları",
    "GARAN": "Garanti BBVA",
    "AKBNK": "Akbank",
    "ISCTR": "İş Bankası",
    "SISE": "Şişecam",
    "BIMAS": "BİM Mağazacılık",
    "EREGL": "Erdemir",
    "KCHOL": "Koç Holding",
    "SAHOL": "Sabancı Holding",
    "TUPRS": "Tüpraş",
    "ASELS": "Aselsan",
    "YKBNK": "Yapı Kredi Bankası",
    "VAKBN": "VakıfBank",
    "HALKB": "Halkbank",
    "ZOREN": "Zorlu Enerji",
    "PETKM": "Petkim",
    "PGSUS": "Pegasus",
    "SASA": "Sasa Polyester",
    "TCELL": "Turkcell",
    "TTKOM": "Türk Telekom",
    "TOASO": "Tofaş Oto",
    "FROTO": "Ford Otosan",
    "ENKAI": "Enka İnşaat",
    "EKGYO": "Emlak Konut GYO",
    "KOZAL": "Koza Altın",
    "KOZAA": "Koza Madencilik",
    "IPEKE": "İpek Doğal Enerji",
    "ASTOR": "Astor Enerji",
    "KONTR": "Kontrolmatik",
    "MGROS": "Migros",
    "ODAS": "Odaş Elektrik",
    "ALARK": "Alarko Holding",
    "BRSAN": "Borusan Mannesmann",
    "GUBRF": "Gübre Fabrikaları",
    "HEKTS": "Hektaş",
    "KRDMD": "Kardemir (D)",
    "OYAKC": "Oyak Çimento",
    "ARCLK": "Arçelik",
    "DOHOL": "Doğan Holding",
    "DOAS": "Doğuş Otomotiv",
    "CIMSA": "Çimsa",
    "ALBRK": "Albaraka Türk",
    "TSKB": "TSKB",
    "YATAS": "Yataş",
    "VESTL": "Vestel",
    "VESBE": "Vestel Beyaz Eşya",
    "SMRTG": "Smart Güneş Enerjisi",
    "SOKM": "Şok Marketler",
    "TAVHL": "TAV Havalimanları",
    "TKFEN": "Tekfen Holding",
    "ZRGYO": "Ziraat GYO",
    "AGHOL": "Anadolu Grubu Holding",
    "CCOLA": "Coca-Cola İçecek",
    "MAVI": "Mavi Giyim",
    "MIATK": "Mia Teknoloji",
    "REEDR": "Reeder Teknoloji",
}

def _get_company_name(symbol: str, ticker: yf.Ticker) -> str:
    base = _clean_symbol(symbol)
    if base in BIST_COMPANY_NAMES:
        return BIST_COMPANY_NAMES[base]
    try:
        info = ticker.info
        name = info.get('shortName') or info.get('longName') or ''
        if name:
            return name.strip()
    except Exception:
        pass
    return ""

@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    """
    Fetch the latest quote and daily change for a symbol using yfinance.
    For BIST, symbols usually end with .IS (e.g. THYAO.IS).
    """
    try:
        # Ensure BIST symbols have .IS suffix
        base_symbol = _clean_symbol(symbol)
        yf_symbol = f"{base_symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        
        # Get today's data
        time.sleep(random.uniform(0.1, 0.5))  # Random delay to prevent rate limiting
        hist = ticker.history(period="5d")
        hist = hist.dropna(subset=['Close'])
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

        company_name = _get_company_name(symbol, ticker)

        return {
            "symbol": symbol,
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "name": company_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}")
def get_signals(symbol: str):
    """
    Fetch technical analysis signals (Strong Buy, Buy, Sell, etc.) from TradingView
    across multiple timeframes.
    """
    try:
        tv_symbol = _clean_symbol(symbol)
        
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
                time.sleep(random.uniform(0.1, 0.5))  # Random delay to prevent rate limiting
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch TV signals: {str(e)}")

@router.get("/chart/{symbol}")
def get_chart_data(symbol: str, interval: str = "1d"):
    """
    Fetch OHLCV data for charts, along with EMA and Volume MA indicators.
    """
    try:
        base_symbol = _clean_symbol(symbol)
        yf_symbol = f"{base_symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        
        # Define period based on interval
        period = "1y" if interval in ["1d", "1wk", "1mo"] else "60d"
        time.sleep(random.uniform(0.1, 0.5))  # Random delay to prevent rate limiting
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chart data: {str(e)}")

