"""
Kullanım:
    pip install -r requirements.txt
    python main.py

.env dosyası oluştur ve içine DeepSeek key'ini koy:
    DEEPSEEK_API_KEY=sk-xxxxx
"""
import json
import config
from data import fiyat_verisi_cek
from strategy import sinyal_uret, son_sinyal
from backtest import backtest_calistir
from ai_advisor import sinyal_yorumla


def portfoy_yukle(path: str = config.PORTFOLIO_FILE) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    portfoy = portfoy_yukle()
    tickers = [p["ticker"] for p in portfoy["positions"]] + portfoy.get("watchlist", [])
    tickers = list(dict.fromkeys(tickers))  # tekrarları temizle

    print(f"Takip edilen hisseler: {tickers}\n")

    for ticker in tickers:
        print(f"{'=' * 50}\n{ticker}\n{'=' * 50}")
        try:
            df = fiyat_verisi_cek(ticker, config.BACKTEST_BASLANGIC, config.BACKTEST_BITIS)
        except ValueError as e:
            print(f"Atlanıyor: {e}\n")
            continue

        df = sinyal_uret(df)

        # Güncel sinyal
        ozet = son_sinyal(df)
        print(f"Güncel sinyal: {ozet['sinyal']} | Kapanış: {ozet['kapanis']} TL | RSI: {ozet['rsi']}")

        # Backtest
        sonuc = backtest_calistir(df)
        print(f"Backtest getirisi: %{sonuc['getiri_pct']} (Al-Tut: %{sonuc['al_tut_getiri_pct']}) | İşlem sayısı: {sonuc['islem_sayisi']}")

        # DeepSeek yorumu
        portfoy_pozisyonu = next((p for p in portfoy["positions"] if p["ticker"] == ticker), None)
        baglam = f"Elimde {portfoy_pozisyonu['adet']} adet, maliyet {portfoy_pozisyonu['maliyet']} TL" if portfoy_pozisyonu else "Watchlist'te, elimde yok"
        yorum = sinyal_yorumla(ticker, ozet, baglam)
        print(f"\nDeepSeek yorumu:\n{yorum}\n")


if __name__ == "__main__":
    main()
