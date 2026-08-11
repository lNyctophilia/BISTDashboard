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
    Fetch OHLCV data for charts, along with EMA, SMA, Bollinger Bands, RSI, MACD and Volume MA indicators.
    """
    try:
        base_symbol = _clean_symbol(symbol)
        yf_symbol = f"{base_symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        
        # Define period based on interval and handle 4h resampling
        time.sleep(random.uniform(0.1, 0.5))  # Random delay to prevent rate limiting
        if interval == "4h":
            hist = ticker.history(period="1y", interval="1h")
            if not hist.empty:
                logic = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
                hist = hist.resample('4h').apply(logic).dropna(subset=['Close'])
        else:
            period = "2y" if interval in ["1d", "1wk", "1mo"] else "1y"
            hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No chart data available")
            
        # Calculate EMA (20 period)
        hist['EMA'] = hist['Close'].ewm(span=20, adjust=False).mean()
        
        # Calculate SMA (50 period)
        hist['SMA50'] = hist['Close'].rolling(window=50, min_periods=1).mean()

        # Calculate Volume MA (20 period)
        hist['VolumeMA'] = hist['Volume'].rolling(window=20, min_periods=1).mean()
        
        # Calculate Bollinger Bands (20 period, 2 std)
        boll_mid = hist['Close'].rolling(window=20, min_periods=1).mean()
        boll_std = hist['Close'].rolling(window=20, min_periods=1).std().fillna(0)
        hist['BollMiddle'] = boll_mid
        hist['BollUpper'] = boll_mid + (boll_std * 2)
        hist['BollLower'] = boll_mid - (boll_std * 2)

        # Calculate RSI (14 period)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / (loss.replace(0, 1e-9))
        hist['RSI'] = 100 - (100 / (1 + rs))

        # Calculate MACD (12, 26, 9)
        ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = ema12 - ema26
        hist['MACDSignal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        hist['MACDHist'] = hist['MACD'] - hist['MACDSignal']

        # Handle NaN values
        hist = hist.fillna(0)
        
        data = []
        for index, row in hist.iterrows():
            c_val = float(row['Close'])
            data.append({
                "time": int(index.timestamp() * 1000), # milliseconds
                "open": round(float(row['Open']), 2),
                "high": round(float(row['High']), 2),
                "low": round(float(row['Low']), 2),
                "close": round(c_val, 2),
                "volume": int(row['Volume']),
                "ema": round(float(row['EMA']), 2) if row['EMA'] > 0 else None,
                "sma_50": round(float(row['SMA50']), 2) if row['SMA50'] > 0 else None,
                "volume_ma": int(row['VolumeMA']) if row['VolumeMA'] > 0 else None,
                "bollinger_upper": round(float(row['BollUpper']), 2) if row['BollUpper'] > 0 else None,
                "bollinger_middle": round(float(row['BollMiddle']), 2) if row['BollMiddle'] > 0 else None,
                "bollinger_lower": round(float(row['BollLower']), 2) if row['BollLower'] > 0 else None,
                "rsi": round(float(row['RSI']), 2) if row['RSI'] > 0 else None,
                "macd": round(float(row['MACD']), 2),
                "macd_signal": round(float(row['MACDSignal']), 2),
                "macd_hist": round(float(row['MACDHist']), 2),
            })

        # Calculate Pivot Points & Support / Resistance
        last_30 = hist.tail(30)
        recent_high = float(last_30['High'].max())
        recent_low = float(last_30['Low'].min())
        recent_close = float(last_30['Close'].iloc[-1])
        
        pivot = round((recent_high + recent_low + recent_close) / 3, 2)
        r1 = round((2 * pivot) - recent_low, 2)
        s1 = round((2 * pivot) - recent_high, 2)
        r2 = round(pivot + (recent_high - recent_low), 2)
        s2 = round(pivot - (recent_high - recent_low), 2)
        
        support_resistance = {
            "pivot": pivot,
            "r1": r1,
            "s1": s1,
            "r2": r2,
            "s2": s2,
        }
            
        return {
            "symbol": symbol,
            "interval": interval,
            "data": data,
            "support_resistance": support_resistance,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chart data: {str(e)}")


