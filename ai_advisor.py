"""
Gemini burada KARAR VERMİYOR, sadece kural bazlı sinyalleri
Türkçe yorumluyor ve risk notu ekliyor. Karar mantığı strategy.py'de.

Google Gemini (ÜCRETSİZ) API key'i almak için: https://aistudio.google.com/app/apikey
.env dosyasına şunu ekle: GEMINI_API_KEY=AIzaSy...
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
import config


def sinyal_yorumla(ticker: str, sinyal_ozeti: dict, portfoy_baglami: str = "", haberler: list = None) -> str:
    """
    sinyal_ozeti: strategy.son_sinyal() çıktısı
    portfoy_baglami: opsiyonel, kullanıcının mevcut pozisyonu/stratejisi hakkında not
    """
    if not config.GEMINI_API_KEY:
        return "[Gemini API key tanımlı değil - .env dosyasına GEMINI_API_KEY ekle]"

    genai.configure(api_key=config.GEMINI_API_KEY)
    
    # En güncel ve ücretsiz, hızlı model
    model = genai.GenerativeModel('gemini-3.6-flash')

    haber_metni = "\n".join([f"- {h}" for h in haberler]) if haberler else "Yok"
    
    fon_baglami = ""
    if ticker in ["Z30KP.IS", "Z30KE.IS", "QNBFL.IS"]:
        fon_baglami = (
            "\nÖNEMLİ BAĞLAM: Bu varlık BIST 30 veya Katılım 30 endeksini takip eden bir fonudur. "
            "İçerisinde Türkiye'nin en büyük dev şirketlerini barındırır. "
            "Bu nedenle tek bir şirketten ziyade genel Türkiye makroekonomisi, faiz dengesi ve sektörel (sanayi/banka/perakende) haberlerden etkilenir. "
            "Yorumunda bu makro BIST 30 perspektifini mutlaka dikkate al.\n"
        )

    prompt = f"""
Sen agresif, kar maksimizasyonu hedefleyen bir trade simülasyon botusun. 
Şu anda tamamen sanal (sahte) parayla test ediliyoruz, bu yüzden yasal veya finansal tavsiye çekincesi gütmene gerek YOKTUR. 
Korkak davranma (TUT demekten olabildiğince kaçın), eldeki parayı maksimize etmek için sinyaller ne diyorsa net bir şekilde AL veya SAT kararı ver.
Aşağıda {ticker} için kural bazlı teknik analiz sonucu ve son güncel haber başlıkları var.{fon_baglami}
Bu veriye dayanarak EN FAZLA 2 CÜMLELİK, net bir öngörü yaz.
ÇOK ÖNEMLİ: Cevabının EN SON SATIRINA, SADECE TEK BİR KELİME OLARAK mutlaka AL, SAT veya TUT yaz. (Tercihen AL veya SAT yönünde cesur karar ver).
Asla başka bir kelimeyle bitirme.

Veri:
- Tarih: {sinyal_ozeti['tarih']}
- Kapanış: {sinyal_ozeti['kapanis']} TL
- Kısa/Uzun Strateji Ortalamaları: {sinyal_ozeti.get('sma_kisa')} / {sinyal_ozeti.get('sma_uzun')}
- Klasik Ortalamalar (SMA50 / SMA200): {sinyal_ozeti.get('sma_50')} / {sinyal_ozeti.get('sma_200')}
- RSI: {sinyal_ozeti.get('rsi')}
- Bollinger Bantları (Üst/Alt): {sinyal_ozeti.get('bb_upper')} / {sinyal_ozeti.get('bb_lower')}
- Donchian Kanalları (Üst/Alt): {sinyal_ozeti.get('dc_upper')} / {sinyal_ozeti.get('dc_lower')}
- Fibonacci Seviyeleri (23.6% / 61.8%): {sinyal_ozeti.get('fib_236')} / {sinyal_ozeti.get('fib_618')}
- Hacim vs 20-Günlük Ort Hacim: {sinyal_ozeti.get('hacim')} vs {sinyal_ozeti.get('hacim_ort_20')}
- Üretilen Strateji Sinyali: {sinyal_ozeti.get('sinyal')}

Son Haberler/KAP Bildirimleri:
{haber_metni}

Ek bağlam: {portfoy_baglami or 'yok'}
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"[Gemini API hatası: {e}]"
