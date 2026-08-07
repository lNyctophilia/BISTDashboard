"""
BIST fiyat verisini tvDatafeed (TradingView) üzerinden çeker.
Küresel varlıklar için yfinance kullanılmaya devam eder.
"""
import yfinance as yf
import pandas as pd
from tvDatafeed import TvDatafeed, Interval
import logging

# tvDatafeed nologin uyarısını gizle
logging.getLogger('tvDatafeed').setLevel(logging.ERROR)
tv = TvDatafeed()

def fiyat_verisi_cek(ticker: str, baslangic: str, bitis: str, interval: str = "1d") -> pd.DataFrame:
    """
    Belirtilen hisse için OHLCV verisini indirir.
    BIST hisseleri (.IS) için TradingView, diğerleri için yfinance kullanır.
    """
    if ticker.endswith(".IS"):
        sembol = ticker.replace(".IS", "")
        # tvDatafeed ile 1000 bar (yaklaşık 4 yıllık iş günü) çek
        df = tv.get_hist(symbol=sembol, exchange='BIST', interval=Interval.in_daily, n_bars=1000)
        
        if df is None or df.empty:
            raise ValueError(f"{ticker} için TradingView'da veri bulunamadı. Ticker adını kontrol et.")
            
        # Sütunları yfinance formatına dönüştür
        df = df.rename(columns={
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume"
        })
        if "symbol" in df.columns:
            df = df.drop(columns=["symbol"])
            
        # Saatleri sıfırla ve tarihe göre filtrele
        df.index = df.index.normalize()
        if baslangic:
            df = df.loc[df.index >= pd.to_datetime(baslangic)]
        if bitis:
            df = df.loc[df.index <= pd.to_datetime(bitis)]
            
    else:
        df = yf.download(ticker, start=baslangic, end=bitis, interval=interval, progress=False)
        if df.empty:
            raise ValueError(f"{ticker} için veri bulunamadı. Ticker adını kontrol et.")
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
    df = df.dropna()
    return df


def haberleri_cek(ticker: str, limit: int = 3) -> list:
    """
    Belirtilen hisse için son haber başlıklarını çeker. Altın BYF'leri ise küresel altın (GC=F) haberlerini çeker.
    """
    # Altın ve Gümüş fonları için küresel vadelileri aratmak daha doğru sonuç verir
    altin_byf = ["ZGOLD.IS", "GLDTR.IS", "KUTL.IS", "GGK.IS"]
    gumus_byf = ["GMTR.IS"]
    bist_byf = ["Z30KP.IS", "Z30KE.IS", "QNBFL.IS"] # BIST endeks fonları
    
    if ticker in altin_byf:
        hedef_ticker = "GC=F"
    elif ticker in gumus_byf:
        hedef_ticker = "SI=F" # Küresel Gümüş Vadelileri
    elif ticker in bist_byf:
        hedef_ticker = "TUR" # iShares MSCI Turkey ETF (Genel Türkiye haberleri için)
    else:
        hedef_ticker = ticker
    
    try:
        tkr = yf.Ticker(hedef_ticker)
        news_data = tkr.news
        haberler = []
        for n in news_data[:limit]:
            if 'content' in n and 'title' in n['content']:
                haberler.append(n['content']['title'])
            elif 'title' in n:
                haberler.append(n['title'])
        return haberler
    except Exception as e:
        return []

def portfoy_verisi_cek(tickers: list[str], baslangic: str, bitis: str) -> dict[str, pd.DataFrame]:
    """Birden fazla hisse için veriyi tek seferde çeker."""
    veriler = {}
    for t in tickers:
        try:
            veriler[t] = fiyat_verisi_cek(t, baslangic, bitis)
        except ValueError as e:
            print(f"Uyarı: {e}")
    return veriler
