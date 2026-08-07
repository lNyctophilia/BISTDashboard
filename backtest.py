"""
Basit backtest: AL sinyalinde tüm nakit ile pozisyon aç, SAT sinyalinde kapat.
Komisyon/kayma (slippage) dahil değil - gerçekçi sonuç için ekleyebilirsin.
"""
import pandas as pd
import config


def backtest_calistir(df: pd.DataFrame, baslangic_sermaye: float = None) -> dict:
    sermaye = baslangic_sermaye or config.BASLANGIC_SERMAYE
    nakit = sermaye
    adet = 0
    islemler = []

    for tarih, row in df.iterrows():
        fiyat = row["Close"]
        sinyal = row["sinyal"]

        if sinyal == "AL" and nakit > 0:
            adet = nakit / fiyat
            nakit = 0
            islemler.append({"tarih": str(tarih.date()), "islem": "AL", "fiyat": round(fiyat, 2), "adet": round(adet, 2)})

        elif sinyal == "SAT" and adet > 0:
            nakit = adet * fiyat
            islemler.append({"tarih": str(tarih.date()), "islem": "SAT", "fiyat": round(fiyat, 2), "tutar": round(nakit, 2)})
            adet = 0

    son_fiyat = df["Close"].iloc[-1]
    bitis_degeri = nakit + (adet * son_fiyat)
    getiri_pct = ((bitis_degeri - sermaye) / sermaye) * 100

    # Kıyas: aynı dönemde "al ve tut" stratejisi ne yapardı
    ilk_fiyat = df["Close"].iloc[0]
    al_tut_getiri = ((son_fiyat - ilk_fiyat) / ilk_fiyat) * 100

    return {
        "baslangic_sermaye": sermaye,
        "bitis_degeri": round(bitis_degeri, 2),
        "getiri_pct": round(getiri_pct, 2),
        "al_tut_getiri_pct": round(al_tut_getiri, 2),
        "islem_sayisi": len(islemler),
        "islemler": islemler,
    }
