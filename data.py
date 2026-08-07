"""
BIST fiyat verisini yfinance üzerinden çeker.
Not: yfinance BIST hisseleri için '.IS' uzantısı ister (örn THYAO.IS).
"""
import yfinance as yf
import pandas as pd


def fiyat_verisi_cek(ticker: str, baslangic: str, bitis: str, interval: str = "1d") -> pd.DataFrame:
    """
    Belirtilen hisse için OHLCV verisini indirir.
    Dönüş: DataFrame (index=tarih, sütunlar=Open/High/Low/Close/Volume)
    """
    df = yf.download(ticker, start=baslangic, end=bitis, interval=interval, progress=False)
    if df.empty:
        raise ValueError(f"{ticker} için veri bulunamadı. Ticker adını kontrol et.")
    
    # Yeni yfinance sürümünde tek hisse bile olsa MultiIndex sütun dönebiliyor, bunu düzeltiyoruz
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
    
    if ticker in altin_byf:
        hedef_ticker = "GC=F"
    elif ticker in gumus_byf:
        hedef_ticker = "SI=F" # Küresel Gümüş Vadelileri
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
