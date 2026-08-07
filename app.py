import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import config
from data import fiyat_verisi_cek, haberleri_cek
from strategy import sinyal_uret, son_sinyal
from backtest import backtest_calistir
from ai_advisor import sinyal_yorumla

def portfoy_yukle(path=config.PORTFOLIO_FILE):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"positions": [], "watchlist": []}

class PortfoyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Portföy ve Trend Takip Asistanı")
        self.root.geometry("800x600")
        
        self.portfoy = portfoy_yukle()
        
        positions = [p["ticker"] for p in self.portfoy["positions"]]
        watchlist = self.portfoy.get("watchlist", [])
        self.tum_semboller = list(dict.fromkeys(positions + watchlist))
        
        self._arayuz_olustur()
        
    def _arayuz_olustur(self):
        # Üst Kısım: Seçim ve Buton
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill=tk.X)
        
        ttk.Label(frame_top, text="Analiz Edilecek Varlık:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        
        self.combo_sembol = ttk.Combobox(frame_top, values=self.tum_semboller, state="readonly", font=("Arial", 12), width=20)
        if self.tum_semboller:
            self.combo_sembol.current(0)
        self.combo_sembol.pack(side=tk.LEFT, padx=5)
        
        self.btn_analiz = ttk.Button(frame_top, text="Analizi Başlat", command=self.analiz_baslat)
        self.btn_analiz.pack(side=tk.LEFT, padx=10)
        
        # Orta Kısım: Çıktı Ekranı
        frame_mid = ttk.Frame(self.root, padding=10)
        frame_mid.pack(fill=tk.BOTH, expand=True)
        
        self.text_cikti = tk.Text(frame_mid, font=("Consolas", 11), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(frame_mid, command=self.text_cikti.yview)
        self.text_cikti.configure(yscrollcommand=scrollbar.set)
        
        self.text_cikti.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Renk tagları tanımlayalım
        self.text_cikti.tag_config("AL", foreground="green", font=("Consolas", 12, "bold"))
        self.text_cikti.tag_config("SAT", foreground="red", font=("Consolas", 12, "bold"))
        self.text_cikti.tag_config("TUT", foreground="#b8860b", font=("Consolas", 12, "bold")) # Dark goldenrod
        
        self.yazdir("Uygulama hazır. Lütfen bir varlık seçip 'Analizi Başlat' butonuna tıklayın.\n")
        
    def yazdir(self, metin, tag=None):
        if tag:
            self.text_cikti.insert(tk.END, metin + "\n", tag)
        else:
            self.text_cikti.insert(tk.END, metin + "\n")
        self.text_cikti.see(tk.END)
        self.root.update_idletasks()
        
    def ekran_temizle(self):
        self.text_cikti.delete(1.0, tk.END)

    def analiz_baslat(self):
        secili_sembol = self.combo_sembol.get()
        if not secili_sembol:
            messagebox.showwarning("Uyarı", "Lütfen bir sembol seçin.")
            return
            
        self.btn_analiz.config(state=tk.DISABLED)
        self.ekran_temizle()
        self.yazdir(f"[{secili_sembol}] Analizi Başlıyor...\nLütfen bekleyin, veriler çekiliyor ve Gemini AI'ye bağlanılıyor...\n")
        
        # Arayüzün donmaması için arka planda (thread) çalıştırıyoruz
        threading.Thread(target=self.islem_thread, args=(secili_sembol,), daemon=True).start()

    def islem_thread(self, sembol):
        try:
            # 1. Veri Çekme
            self.root.after(0, self.yazdir, "Aşama 1: Fiyat verileri indiriliyor...")
            df = fiyat_verisi_cek(sembol, config.BACKTEST_BASLANGIC, config.BACKTEST_BITIS)
            
            # 2. Haberleri Çekme
            self.root.after(0, self.yazdir, "Aşama 2: Son haberler/KAP bildirimleri aranıyor...")
            haberler = haberleri_cek(sembol, limit=3)
            
            # 3. Hesaplamalar
            self.root.after(0, self.yazdir, "Aşama 3: Teknik göstergeler hesaplanıyor...")
            df = sinyal_uret(df)
            ozet = son_sinyal(df)
            sonuc = backtest_calistir(df)
            
            self.root.after(0, self.yazdir, "-"*60)
            self.root.after(0, self.yazdir, f"📉 TEKNİK ÖZET: {sembol}")
            self.root.after(0, self.yazdir, f"Son Kapanış      : {ozet['kapanis']:.2f} TL")
            self.root.after(0, self.yazdir, f"Güncel Sinyal    : {ozet['sinyal']}")
            self.root.after(0, self.yazdir, f"SMA (50/200)     : {ozet.get('sma_50')} / {ozet.get('sma_200')}")
            rsi_val = f"{ozet['rsi']:.1f}" if ozet.get('rsi') is not None else "Yetersiz Veri"
            self.root.after(0, self.yazdir, f"RSI (14)         : {rsi_val}")
            if ozet.get('bb_upper'):
                self.root.after(0, self.yazdir, f"Bollinger Bant   : {ozet.get('bb_lower')} - {ozet.get('bb_upper')}")
            if ozet.get('dc_upper'):
                self.root.after(0, self.yazdir, f"Donchian Kanalı  : {ozet.get('dc_lower')} - {ozet.get('dc_upper')}")
            if ozet.get('fib_618'):
                self.root.after(0, self.yazdir, f"Fibonacci (61.8%): {ozet.get('fib_618')}")
            if ozet.get('hacim'):
                self.root.after(0, self.yazdir, f"Hacim / Ort (20) : {ozet.get('hacim')} / {ozet.get('hacim_ort_20')}")
            self.root.after(0, self.yazdir, f"Backtest Getirisi: %{sonuc['getiri_pct']:.1f} (Al-Tut: %{sonuc['al_tut_getiri_pct']:.1f})")
            self.root.after(0, self.yazdir, "-"*60)
            
            if haberler:
                self.root.after(0, self.yazdir, f"📰 SON HABERLER / BİLDİRİMLER:")
                for h in haberler:
                    self.root.after(0, self.yazdir, f"- {h}")
                self.root.after(0, self.yazdir, "-"*60)
            
            # 4. AI Yorumu
            self.root.after(0, self.yazdir, "\n🤖 YAPAY ZEKA YORUMU EKLENİYOR...\n")
            portfoy_pozisyonu = next((p for p in self.portfoy["positions"] if p["ticker"] == sembol), None)
            if portfoy_pozisyonu:
                baglam = f"Elimde {portfoy_pozisyonu['adet']} adet, maliyet {portfoy_pozisyonu['maliyet']} TL"
            else:
                baglam = "Watchlist'te, elimde yok"
                
            yorum = sinyal_yorumla(sembol, ozet, baglam, haberler=haberler)
            
            self.root.after(0, self.yazdir, "🤖 YAPAY ZEKA YORUMU (GEMINI):\n")
            
            # AI yorumunun son satırındaki AL/SAT/TUT kelimesini ayıklayalım
            lines = [line.strip() for line in yorum.strip().split("\n") if line.strip()]
            if lines:
                son_satir = lines[-1].upper()
                if son_satir in ["AL", "SAT", "TUT"]:
                    # Son kelimeyi renklendirerek yazdır, geri kalanı normal yazdır
                    normal_yorum = "\n".join(lines[:-1])
                    self.root.after(0, self.yazdir, normal_yorum)
                    self.root.after(0, lambda: self.yazdir(f"\nSON KARAR: {son_satir}", son_satir))
                else:
                    self.root.after(0, self.yazdir, yorum)
            else:
                self.root.after(0, self.yazdir, yorum)
                
            self.root.after(0, self.yazdir, "\n" + "="*60 + "\n")
            
        except Exception as e:
            self.root.after(0, self.yazdir, f"\n❌ HATA OLUŞTU: {e}\n")
        finally:
            self.root.after(0, lambda: self.btn_analiz.config(state=tk.NORMAL))


def main():
    root = tk.Tk()
    
    # Modern bir tema uygulamaya çalışalım
    try:
        root.tk.call("source", "azure.tcl") # Eğer azure tema varsa (opsiyonel)
        root.tk.call("set_theme", "light")
    except:
        pass # Standart tema kullan

    app = PortfoyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
