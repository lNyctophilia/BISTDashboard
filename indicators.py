"""
Teknik gösterge hesaplamaları. Hepsi pandas Series alır, Series döner.
"""
import pandas as pd


def sma(seri: pd.Series, pencere: int) -> pd.Series:
    """Basit hareketli ortalama (T günlük)."""
    return seri.rolling(window=pencere).mean()


def ema(seri: pd.Series, pencere: int) -> pd.Series:
    """Üstel hareketli ortalama."""
    return seri.ewm(span=pencere, adjust=False).mean()


def rsi(seri: pd.Series, periyot: int = 14) -> pd.Series:
    """Relative Strength Index - aşırı alım/satım göstergesi (0-100)."""
    delta = seri.diff()
    kazanc = delta.clip(lower=0)
    kayip = -delta.clip(upper=0)
    ort_kazanc = kazanc.rolling(window=periyot).mean()
    ort_kayip = kayip.rolling(window=periyot).mean()
    rs = ort_kazanc / ort_kayip.replace(0, 1e-10)
    return 100 - (100 / (1 + rs))


def macd(seri: pd.Series, hizli: int = 12, yavas: int = 26, sinyal: int = 9):
    """MACD çizgisi ve sinyal çizgisini döner (macd_line, signal_line)."""
    ema_hizli = ema(seri, hizli)
    ema_yavas = ema(seri, yavas)
    macd_line = ema_hizli - ema_yavas
    signal_line = ema(macd_line, sinyal)
    return macd_line, signal_line

def bollinger_bands(seri: pd.Series, pencere: int = 20, num_std: int = 2):
    """Bollinger Bantları: upper_band, mid_band, lower_band döner."""
    mid_band = sma(seri, pencere)
    std_dev = seri.rolling(window=pencere).std()
    upper_band = mid_band + (std_dev * num_std)
    lower_band = mid_band - (std_dev * num_std)
    return upper_band, mid_band, lower_band

def donchian_channels(high_seri: pd.Series, low_seri: pd.Series, pencere: int = 20):
    """Donchian Kanalları: en yüksek yüksek, en düşük düşük döner."""
    upper_channel = high_seri.rolling(window=pencere).max()
    lower_channel = low_seri.rolling(window=pencere).min()
    return upper_channel, lower_channel

def fibonacci_retracement(high_seri: pd.Series, low_seri: pd.Series, pencere: int = 200):
    """
    Son N periyottaki zirve ve dipe göre Fibonacci düzeltme seviyelerini döner.
    Geri dönüş (dict): {'zirve': X, 'dip': Y, 'fib_236': Z, 'fib_382': W, 'fib_500': ..., 'fib_618': ...}
    """
    zirve = high_seri.rolling(window=pencere).max()
    dip = low_seri.rolling(window=pencere).min()
    fark = zirve - dip
    
    return {
        "zirve": zirve,
        "dip": dip,
        "fib_236": zirve - fark * 0.236,
        "fib_382": zirve - fark * 0.382,
        "fib_500": zirve - fark * 0.500,
        "fib_618": zirve - fark * 0.618,
        "fib_786": zirve - fark * 0.786
    }
