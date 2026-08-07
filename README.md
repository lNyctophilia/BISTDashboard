# BIST Trend Takip + DeepSeek Yorumlayıcı (Prototip)

## Kurulum
```bash
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını aç, DEEPSEEK_API_KEY=sk-... satırına kendi key'ini yapıştır
# DeepSeek key'i şuradan alınır: https://platform.deepseek.com
```

## portfolio.json'u kendi verinle doldur
- `positions`: elindeki hisseler (ticker, adet, maliyet, alış tarihi)
- `watchlist`: takip etmek istediğin ama almadığın hisseler
- Ticker formatı: BIST hisseleri için `.IS` uzantısı gerekli (örn `THYAO.IS`)

## Çalıştır
```bash
python main.py
```

## Ne yapıyor?
1. `data.py` → yfinance ile geçmiş fiyat verisini çeker
2. `strategy.py` → SMA kesişimi + RSI'ye dayalı **kural bazlı** AL/SAT sinyali üretir
   (T günlük pencereler `config.py`'de `KISA_T` / `UZUN_T` olarak ayarlanır)
3. `backtest.py` → bu kuralları geçmiş veride sanal parayla test eder, "al-tut" ile kıyaslar
4. `deepseek_advisor.py` → üretilen sinyali DeepSeek'e yorumlatır (DeepSeek karar vermez,
   sadece gerekçe/risk yorumu yazar — bilinçli bir tasarım tercihi, LLM'e "al/sat" kararını
   bırakmak riskli)

## Sıradaki adımlar (istersen)
- Komisyon/kayma (slippage) ekleyerek backtest'i gerçekçileştirmek
- Stop-loss / take-profit kuralları eklemek
- Paper trading için günlük otomatik çalıştırma (cron / GitHub Actions)
- Sonuçları bir dashboard'da göstermek (Streamlit ile hızlıca yapılabilir)

## Uyarı
Bu bir prototiptir, yatırım tavsiyesi değildir. Gerçek parayla kullanmadan önce
backtest sonuçlarını iyice incele, küçük miktarla paper trading yap.
