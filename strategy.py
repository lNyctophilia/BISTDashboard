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

    # Temel Kesişimler (Kısa / Uzun SMA)
    kisa_uzeri = df["sma_kisa"] > df["sma_uzun"]
    kisa_uzeri_onceki = kisa_uzeri.shift(1)

    altin_kesisim = kisa_uzeri & (~kisa_uzeri_onceki.astype(bool))
    olum_kesisimi = (~kisa_uzeri) & (kisa_uzeri_onceki.astype(bool))

    # Ek İndikatör Filtreleri
    macd_al = df["macd_line"] > df["macd_signal"]
    macd_sat = df["macd_line"] < df["macd_signal"]
    
    # Fiyatın uzun vadeli trendin (SMA 50) üzerinde olup olmadığı
    trend_olumlu = df["Close"] > df["sma_50"]
    
    # YENİ: SMA 50'nin yönü yukarı mı? (Son 3 güne göre)
    trend_yon_yukari = df["sma_50"] > df["sma_50"].shift(3)

    # Bollinger alt bandından yukarı sekme (Aşırı satımdan dönüş tepkisi)
    bb_alttan_donus = (df["Close"] > df["bb_lower"]) & (df["Close"].shift(1) <= df["bb_lower"].shift(1))
    
    # Bollinger üst bandından aşağı dönüş (Aşırı alımdan dönüş)
    bb_ustten_donus = (df["Close"] < df["bb_upper"]) & (df["Close"].shift(1) >= df["bb_upper"].shift(1))

    # YENİ: Hacim Onayı (Varsa)
    hacim_onayi = True
    if "Volume" in df.columns and "vol_sma_20" in df.columns:
        hacim_onayi = df["Volume"] > df["vol_sma_20"]

    # --- AL KOŞULU ---
    # 1. Altın kesişim var VEYA (Bollinger alt bandından döndü ve MACD onaylıyor)
    # 2. VE Hacim ortalamanın üzerindeyse (varsa)
    # 3. VE Genel trend olumlu (Fiyat SMA50 üzerinde) VE trendin yönü yukarı
    # 4. VE RSI 70'in altında (Henüz aşırı alıma girmemiş)
    al_kosulu = (
        (altin_kesisim | (bb_alttan_donus & macd_al)) 
        & hacim_onayi 
        & trend_olumlu 
        & trend_yon_yukari 
        & (df["rsi"] < 70)
    )

    # YENİ: Trailing Stop (Süren Stop)
    trailing_stop = False
    if "dc_lower" in df.columns:
        trailing_stop = df["Close"] < df["dc_lower"].shift(1)

    # --- SAT KOŞULU ---
    # 1. Ölüm kesişimi var VEYA
    # 2. Bollinger üst bandından aşağı döndü VEYA
    # 3. RSI 80 üzerinde (Çok aşırı ısınmış - kesin kâr al) VEYA
    # 4. Trend zayıflıyor: MACD sat veriyor ve RSI 70'in üzerinde VEYA
    # 5. Fiyat Donchian alt bandını kırdı (Stop-Loss)
    sat_kosulu = (
        olum_kesisimi 
        | bb_ustten_donus 
        | (df["rsi"] > 80) 
        | (macd_sat & (df["rsi"] > 70))
        | trailing_stop
    )

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
