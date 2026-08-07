"""
Kural bazlı sinyal üretimi. Karar mekanizması burada, DeepSeek DEĞİL -
DeepSeek sadece bu sinyalleri yorumlar (bkz. deepseek_advisor.py).
"""
import pandas as pd
import config
from indicators import sma, rsi, macd, bollinger_bands, donchian_channels, fibonacci_retracement


def sinyal_uret(df: pd.DataFrame) -> pd.DataFrame:
    """
    df: en az 'Close' sütunu olan fiyat verisi.
    Dönüş: orijinal df + 'sinyal' sütunu ('AL' / 'SAT' / 'TUT')
    """
    df = df.copy()
    close = df["Close"]

    df["sma_kisa"] = sma(close, config.KISA_T)
    df["sma_uzun"] = sma(close, config.UZUN_T)
    
    # Yeni eklenen indikatörler (Yapay Zeka bağlamı için)
    df["sma_50"] = sma(close, 50)
    df["sma_200"] = sma(close, 200)
    
    df["rsi"] = rsi(close, config.RSI_PERIYOT)
    df["macd_line"], df["macd_signal"] = macd(close)
    
    # Bollinger Bantları
    df["bb_upper"], df["bb_mid"], df["bb_lower"] = bollinger_bands(close, 20, 2)
    
    # Donchian Kanalları (High, Low sütunları varsa hesapla)
    if "High" in df.columns and "Low" in df.columns:
        df["dc_upper"], df["dc_lower"] = donchian_channels(df["High"], df["Low"], 20)
        
        # Fibonacci
        fib_seviyeler = fibonacci_retracement(df["High"], df["Low"], 200)
        for key, seri in fib_seviyeler.items():
            df[key] = seri
            
    # Hacim analizi (Volume sütunu varsa hesapla)
    if "Volume" in df.columns:
        df["vol_sma_20"] = sma(df["Volume"], 20)
    
    df["sinyal"] = "TUT"

    # Altın kesişim: kısa ortalama uzun ortalamayı yukarı keserse -> AL
    kisa_uzeri = df["sma_kisa"] > df["sma_uzun"]
    kisa_uzeri_onceki = kisa_uzeri.shift(1)

    altin_kesisim = kisa_uzeri & (~kisa_uzeri_onceki.astype(bool))
    olum_kesisimi = (~kisa_uzeri) & (kisa_uzeri_onceki.astype(bool))

    # RSI filtresi: RSI 70 üstündeyse aşırı alım (AL sinyalini zayıflat)
    #               RSI 30 altındaysa aşırı satım (SAT sinyalini zayıflat)
    al_kosulu = altin_kesisim & (df["rsi"] < 70)
    sat_kosulu = olum_kesisimi | (df["rsi"] > 80)  # aşırı ısınmışsa kâr al

    df.loc[al_kosulu, "sinyal"] = "AL"
    df.loc[sat_kosulu, "sinyal"] = "SAT"

    return df


def son_sinyal(df: pd.DataFrame) -> dict:
    """En son günün sinyalini ve gerekçe verilerini özetler."""
    son = df.iloc[-1]
    
    ozet = {
        "tarih": str(df.index[-1].date()),
        "kapanis": round(float(son["Close"]), 2),
        "sinyal": son["sinyal"],
        "sma_kisa": round(float(son["sma_kisa"]), 2) if pd.notna(son["sma_kisa"]) else None,
        "sma_uzun": round(float(son["sma_uzun"]), 2) if pd.notna(son["sma_uzun"]) else None,
        "sma_50": round(float(son["sma_50"]), 2) if pd.notna(son["sma_50"]) else None,
        "sma_200": round(float(son["sma_200"]), 2) if pd.notna(son["sma_200"]) else None,
        "rsi": round(float(son["rsi"]), 2) if pd.notna(son["rsi"]) else None,
        "bb_upper": round(float(son["bb_upper"]), 2) if pd.notna(son["bb_upper"]) else None,
        "bb_lower": round(float(son["bb_lower"]), 2) if pd.notna(son["bb_lower"]) else None,
    }
    
    if "dc_upper" in df.columns:
        ozet["dc_upper"] = round(float(son["dc_upper"]), 2) if pd.notna(son["dc_upper"]) else None
        ozet["dc_lower"] = round(float(son["dc_lower"]), 2) if pd.notna(son["dc_lower"]) else None
        ozet["fib_236"] = round(float(son["fib_236"]), 2) if pd.notna(son["fib_236"]) else None
        ozet["fib_618"] = round(float(son["fib_618"]), 2) if pd.notna(son["fib_618"]) else None
        
    if "Volume" in df.columns and "vol_sma_20" in df.columns:
        ozet["hacim"] = int(son["Volume"]) if pd.notna(son["Volume"]) else None
        ozet["hacim_ort_20"] = int(son["vol_sma_20"]) if pd.notna(son["vol_sma_20"]) else None
        
    return ozet

def aylik_ozetler(df: pd.DataFrame) -> list:
    """Son 3 ayın (Güncel, 1 Ay Önce, 2 Ay Önce, 3 Ay Önce) özet verilerini döndürür."""
    if df.empty:
        return []
    
    ozetler = []
    son_tarih = df.index[-1]
    
    offsets = [0, 1, 2, 3] # aylar
    for offset in offsets:
        hedef_tarih = son_tarih - pd.DateOffset(months=offset)
        # Hedef tarihe en yakın olan geçmiş günü bul
        gecmis_df = df[df.index <= hedef_tarih]
        if not gecmis_df.empty:
            son = gecmis_df.iloc[-1]
            ozetler.append({
                "Zaman": "Güncel" if offset == 0 else f"{offset} Ay Önce",
                "Tarih": str(son.name.date()),
                "Kapanis": round(float(son["Close"]), 2),
                "Sinyal": son.get("sinyal", "TUT"),
                "RSI": round(float(son["rsi"]), 1) if pd.notna(son.get("rsi")) else "Y/V"
            })
    return ozetler
