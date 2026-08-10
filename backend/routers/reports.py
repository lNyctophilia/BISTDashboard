from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pykap

router = APIRouter()

@router.get("/news/{symbol}")
def get_news(symbol: str):
    """
    Fetch recent news for a symbol using yfinance.
    """
    try:
        yf_symbol = symbol if symbol.endswith(".IS") else f"{symbol}.IS"
        ticker = yf.Ticker(yf_symbol)
        news_data = ticker.news
        
        formatted_news = []
        for item in news_data:
            content = item.get("content", {})
            title = content.get("title", "No Title")
            source = content.get("provider", {}).get("displayName", "Yahoo Finance")
            url = content.get("clickThroughUrl", {}).get("url", "#")
            if title != "No Title":
                formatted_news.append({"title": title, "source": source, "url": url})
        
        # Fallback if no news
        if not formatted_news:
            clean_symbol = symbol.replace(".IS", "")
            formatted_news = [
                {"title": f"{clean_symbol} hakkında güncel haber bulunamadı.", "source": "Sistem", "url": "#"}
            ]
            
        return {
            "symbol": symbol,
            "news": formatted_news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kap/{symbol}")
def get_kap_reports(symbol: str):
    """
    Scrape recent KAP reports for the symbol.
    """
    try:
        clean_symbol = symbol.replace(".IS", "")
        
        try:
            comp = pykap.bist.BISTCompany(ticker=clean_symbol)
            disclosures = comp.get_disclosures()
            
            reports = []
            for item in disclosures[:5]:  # Get top 5 recent disclosures
                title = item.get('title', item.get('summary', 'KAP Bildirimi'))
                date = item.get('publishDate', '')
                index = item.get('disclosureIndex', '')
                link = f"https://www.kap.org.tr/tr/Bildirim/{index}" if index else "https://www.kap.org.tr/tr/"
                
                reports.append({
                    "title": title,
                    "date": date,
                    "link": link
                })
        except Exception as e:
            print(f"Pykap error for {clean_symbol}: {e}")
            reports = []
            
        if not reports:
            reports = [
                {"title": f"{clean_symbol} için KAP verisi bulunamadı veya çekilemedi.", "date": "-", "link": "https://www.kap.org.tr/tr/"}
            ]

        return {
            "symbol": symbol,
            "reports": reports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/broker-targets/{symbol}")
def get_broker_targets(symbol: str):
    """
    Scrape broker target prices from Is Yatirim and Yahoo Finance.
    """
    try:
        clean_symbol = symbol.replace(".IS", "").upper()
        targets = []
        
        # 1. Scrape Is Yatirim from Sirket Karti (Covers all sectors)
        try:
            h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            r = requests.get(f'https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={clean_symbol}', headers=h, timeout=5)
            if r.status_code == 200:
                r.encoding = 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')
                
                hedef_fiyat = 0.0
                oneri = "-"
                tarih = "-"
                
                # Fetch Oneri (Recommendation)
                oneri_span = soup.find('span', id='Oneri_Aciklama')
                if oneri_span:
                    oneri = oneri_span.text.strip().capitalize()
                    
                # Fetch Hedef Fiyat and Tarih
                for li in soup.find_all('li'):
                    text = li.text.strip()
                    span = li.find('span')
                    if span:
                        val = span.text.strip()
                        if text.startswith('Hedef Fiyat'):
                            try:
                                hedef_fiyat = float(val.replace(',', '.'))
                            except ValueError:
                                hedef_fiyat = 0.0
                        elif text.startswith('Son ') and 'Tarih' in text:
                            tarih = val
                            
                # If a valid target price was found, add it
                if hedef_fiyat > 0.0:
                    targets.append({
                        "broker": "İş Yatırım", 
                        "target_price": hedef_fiyat, 
                        "recommendation": oneri, 
                        "date": tarih
                    })
        except Exception as e:
            print(f"Is Yatirim scrape error: {e}")
            
        # 2. Get Yahoo Finance Consensus
        try:
            yf_symbol = f"{clean_symbol}.IS"
            ticker = yf.Ticker(yf_symbol)
            mean_target = ticker.info.get("targetMeanPrice")
            if mean_target:
                recoms = ticker.recommendations
                recom_text = "Al"
                if recoms is not None and not recoms.empty:
                    # simplistic logic to determine consensus from the latest month (row 0)
                    latest = recoms.iloc[0]
                    buy = latest.get("buy", 0) + latest.get("strongBuy", 0)
                    sell = latest.get("sell", 0) + latest.get("strongSell", 0)
                    hold = latest.get("hold", 0)
                    if buy > sell and buy > hold:
                        recom_text = "Al"
                    elif sell > buy and sell > hold:
                        recom_text = "Sat"
                    else:
                        recom_text = "Tut"
                
                targets.append({
                    "broker": "Yahoo Konsensüs",
                    "target_price": round(mean_target, 2),
                    "recommendation": recom_text,
                    "date": "Güncel"
                })
        except Exception as e:
            print(f"YFinance target error: {e}")
            
        # Fallback if no targets found
        if not targets:
            targets = [
                {"broker": "Sistem", "target_price": 0.0, "recommendation": "Veri Yok", "date": "-"}
            ]

        return {
            "symbol": symbol,
            "targets": targets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
