"""
Genel ayarlar. DeepSeek API key'ini ortam değişkeninden okuyoruz
(kod içine yazma, .env dosyasına koy).
"""
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Trend hesaplama pencereleri (gün)
KISA_T = 5      # kısa vadeli ortalama penceresi
UZUN_T = 20     # uzun vadeli ortalama penceresi
RSI_PERIYOT = 14

# Backtest ayarları
BACKTEST_BASLANGIC = "2025-01-01"
BACKTEST_BITIS = None
BASLANGIC_SERMAYE = 10000.0  # TL - paper trading için sanal sermaye

PORTFOLIO_FILE = "portfolio.json"
