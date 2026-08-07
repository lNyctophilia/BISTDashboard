import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import config
from data import fiyat_verisi_cek, haberleri_cek
from strategy import sinyal_uret, son_sinyal
from backtest import backtest_calistir
import os
from datetime import datetime

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
        
        self.canvases = [] # To prevent garbage collection of charts
        
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
        self.canvases.clear()

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
            self.root.after(0, self.yazdir, f"📉 GÜNLÜK TEKNİK ÖZET: {sembol}")
            
            def _gunluk_tablo_ekle():
                tree_frame = ttk.Frame(self.text_cikti)
                columns = ("Gösterge", "Değer")
                
                satirlar = [
                    ("Son Kapanış", f"{ozet['kapanis']:.2f} TL"),
                    ("Güncel Sinyal", f"{ozet['sinyal']}"),
                    ("SMA (50/200)", f"{ozet.get('sma_50')} / {ozet.get('sma_200')}"),
                    ("RSI (14)", f"{ozet['rsi']:.1f}" if ozet.get('rsi') is not None else "Yetersiz Veri")
                ]
                if ozet.get('bb_upper'):
                    satirlar.append(("Bollinger Bant", f"{ozet.get('bb_lower')} - {ozet.get('bb_upper')}"))
                if ozet.get('dc_upper'):
                    satirlar.append(("Donchian Kanalı", f"{ozet.get('dc_lower')} - {ozet.get('dc_upper')}"))
                if ozet.get('fib_618'):
                    satirlar.append(("Fibonacci (61.8%)", f"{ozet.get('fib_618')}"))
                if ozet.get('hacim'):
                    satirlar.append(("Hacim / Ort (20)", f"{ozet.get('hacim')} / {ozet.get('hacim_ort_20')}"))
                satirlar.append(("Backtest Getirisi", f"%{sonuc['getiri_pct']:.1f} (Al-Tut: %{sonuc['al_tut_getiri_pct']:.1f})"))

                tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=len(satirlar))
                
                tree.heading("Gösterge", text="Gösterge")
                tree.column("Gösterge", width=200, anchor=tk.W)
                tree.heading("Değer", text="Değer")
                tree.column("Değer", width=300, anchor=tk.W)
                
                tree.pack(fill=tk.X, expand=True, padx=5, pady=5)
                
                for k, v in satirlar:
                    tree.insert("", tk.END, values=(k, v))
                    
                self.text_cikti.window_create(tk.END, window=tree_frame)
                self.text_cikti.insert(tk.END, "\n")
                self.text_cikti.see(tk.END)
                
            self.root.after(0, _gunluk_tablo_ekle)
            self.root.after(0, self.yazdir, "-"*60)
            
            # 3 Aylık Mum Grafiği (Candlestick)
            import mplfinance as mpf
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            df_3m = df.tail(64) # Son 3 ay (yaklaşık 64 işlem günü)
            if not df_3m.empty:
                self.root.after(0, self.yazdir, "📊 3 AYLIK GÖRÜNÜM (MUM GRAFİĞİ):")
                
                def _grafik_ekle():
                    mc = mpf.make_marketcolors(up='g', down='r', inherit=True)
                    s = mpf.make_mpf_style(marketcolors=mc, style='yahoo', gridstyle=':')
                    
                    fig, axes = mpf.plot(df_3m, type='candle', style=s, volume=True, returnfig=True, figsize=(7, 3.5))
                    
                    canvas = FigureCanvasTkAgg(fig, master=self.text_cikti)
                    canvas.draw()
                    self.canvases.append(canvas)
                    
                    self.text_cikti.window_create(tk.END, window=canvas.get_tk_widget())
                    self.text_cikti.insert(tk.END, "\n")
                    self.text_cikti.see(tk.END)
                
                self.root.after(0, _grafik_ekle)
            
            if haberler:
                self.root.after(0, self.yazdir, f"📰 SON HABERLER / BİLDİRİMLER:")
                for h in haberler:
                    self.root.after(0, self.yazdir, f"- {h}")
                self.root.after(0, self.yazdir, "-"*60)
            
            # 4. AI Raporu Oluşturma ve Kaydetme
            self.root.after(0, self.yazdir, "\n📝 AI İÇİN RAPOR DOSYASI OLUŞTURULUYOR...\n")
            portfoy_pozisyonu = next((p for p in self.portfoy["positions"] if p["ticker"] == sembol), None)
            if portfoy_pozisyonu:
                baglam = f"Elimde {portfoy_pozisyonu['adet']} adet, maliyet {portfoy_pozisyonu['maliyet']} TL"
            else:
                baglam = "Watchlist'te, elimde yok"
            
            rapor_icerik = f"SEMBOL: {sembol}\n\n"
            rapor_icerik += f"--- PORTFÖY DURUMU ---\n{baglam}\n\n"
            rapor_icerik += f"--- TEKNİK ÖZET ---\n"
            rapor_icerik += f"Kapanış: {ozet['kapanis']:.2f}\n"
            rapor_icerik += f"Sinyal: {ozet['sinyal']}\n"
            rapor_icerik += f"SMA (50/200): {ozet.get('sma_50')} / {ozet.get('sma_200')}\n"
            if ozet.get('rsi') is not None:
                rapor_icerik += f"RSI (14): {ozet['rsi']:.1f}\n"
            if ozet.get('bb_upper'):
                rapor_icerik += f"Bollinger: {ozet.get('bb_lower')} - {ozet.get('bb_upper')}\n"
            if ozet.get('dc_upper'):
                rapor_icerik += f"Donchian: {ozet.get('dc_lower')} - {ozet.get('dc_upper')}\n"
            if ozet.get('fib_618'):
                rapor_icerik += f"Fibonacci (61.8%): {ozet.get('fib_618')}\n"
            if ozet.get('hacim'):
                rapor_icerik += f"Hacim/Ort: {ozet.get('hacim')} / {ozet.get('hacim_ort_20')}\n\n"
            
            if haberler:
                rapor_icerik += f"--- SON HABERLER ---\n"
                for h in haberler:
                    rapor_icerik += f"- {h}\n"
                rapor_icerik += "\n"
            
            rapor_klasor = "AI_Raporlari"
            os.makedirs(rapor_klasor, exist_ok=True)
            
            zaman = datetime.now().strftime("%Y%m%d_%H%M%S")
            dosya_adi = f"{sembol.replace('.', '_')}_{zaman}.txt"
            dosya_yolu = os.path.join(rapor_klasor, dosya_adi)
            
            with open(dosya_yolu, "w", encoding="utf-8") as f:
                f.write(rapor_icerik)
                
            self.root.after(0, self.yazdir, f"✅ Rapor başarıyla oluşturuldu: {dosya_yolu}")
            self.root.after(0, self.yazdir, "\nLütfen bu dosyayı kopyalayıp Yapay Zekaya atın.")
            self.root.after(0, self.yazdir, "\n" + "="*60 + "\n")
            
        except Exception as e:
            self.root.after(0, self.yazdir, f"\n❌ HATA OLUŞTU: {e}\n")
        finally:
            self.root.after(0, self.baslat_cooldown)

    def baslat_cooldown(self, saniye=25):
        if saniye > 0:
            self.btn_analiz.config(state=tk.DISABLED, text=f"Bekleyin ({saniye}s)")
            self.root.after(1000, self.baslat_cooldown, saniye - 1)
        else:
            self.btn_analiz.config(state=tk.NORMAL, text="Analizi Başlat")

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
