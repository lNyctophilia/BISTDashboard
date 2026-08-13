from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
import cloudscraper
from bs4 import BeautifulSoup
import pykap
import time
import random
import re
import datetime
import io

router = APIRouter()

# Fintables summary cache with 1 hour TTL
_fintables_cache = {}

def fetch_fintables_summary(symbol: str):
    now = time.time()
    clean_sym = symbol.replace(".IS", "").upper()
    
    if clean_sym in _fintables_cache:
        cached = _fintables_cache[clean_sym]
        if now - cached['timestamp'] < 3600:
            return cached['summary'], cached['targets']
            
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': f'https://fintables.com/sirketler/{clean_sym}/analist-tavsiyeleri',
        'Origin': 'https://fintables.com'
    }
    
    summary = None
    targets_list = []
    try:
        scraper = cloudscraper.create_scraper()
        url = f"https://api.fintables.com/analyst-ratings/?code={clean_sym}"
        res = scraper.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            valid_targets = [float(x['price_target']) for x in results if x.get('price_target') is not None]
            in_mp = sum(1 for x in results if x.get('in_model_portfolio'))
            
            for item in results:
                if item.get('price_target') is not None:
                    broker = item.get('brokerage', {}).get('title') or item.get('brokerage', {}).get('short_title') or 'Aracı Kurum'
                    target_p = round(float(item['price_target']), 2)
                    raw_type = (item.get('type') or 'al').upper()
                    rec_map = {
                        'AL': 'Al', 'TUT': 'Tut', 'SAT': 'Sat',
                        'ENDEKS_UZERINDE': 'Endeks Üzeri Getiri',
                        'ENDEKS_USTU': 'Endeks Üzeri Getiri',
                        'ENDEKS_ALTINDA': 'Endeks Altı Getiri',
                        'ENDEKS_PARALEL': 'Endekse Paralel'
                    }
                    rec_text = rec_map.get(raw_type, raw_type.capitalize())
                    pub_date = item.get('published_at', '')
                    date_str = pub_date[:10] if pub_date else 'Güncel'
                    if len(date_str) == 10 and '-' in date_str:
                        p = date_str.split('-')
                        date_str = f"{p[2]}.{p[1]}.{p[0]}"
                    targets_list.append({
                        "broker": broker,
                        "target_price": target_p,
                        "recommendation": rec_text,
                        "date": date_str,
                        "in_model_portfolio": item.get('in_model_portfolio', False)
                    })
            
            if valid_targets:
                avg_target = round(sum(valid_targets) / len(valid_targets), 2)
                min_target = round(min(valid_targets), 2)
                max_target = round(max(valid_targets), 2)
                
                current_price = None
                try:
                    t = yf.Ticker(f"{clean_sym}.IS")
                    fast = t.fast_info
                    current_price = getattr(fast, 'last_price', None) or getattr(fast, 'previous_close', None)
                except Exception:
                    pass
                    
                pot_return = None
                if current_price and current_price > 0:
                    pot_return = round(((avg_target / current_price) - 1) * 100, 2)
                    
                summary = {
                    "avg_target_price": avg_target,
                    "potential_return": pot_return,
                    "target_price_min": min_target,
                    "target_price_max": max_target,
                    "total_recommendations": len(results),
                    "model_portfolio_count": in_mp
                }
    except Exception as e:
        print(f"Fintables analyst ratings error for {clean_sym}: {e}")
        
    if summary is not None or targets_list:
        _fintables_cache[clean_sym] = {'timestamp': now, 'summary': summary, 'targets': targets_list}
    return summary, targets_list






_news_cache = {}

def fetch_fintables_news(symbol: str):
    now = time.time()
    clean_sym = symbol.replace(".IS", "").upper()
    
    if clean_sym in _news_cache:
        cached = _news_cache[clean_sym]
        if now - cached['timestamp'] < 900:
            return cached['data']
            
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': f'https://fintables.com/sirketler/{clean_sym}/akis',
        'Origin': 'https://fintables.com'
    }
    
    formatted_news = []
    try:
        scraper = cloudscraper.create_scraper()
        url = f"https://api.fintables.com/topic-feed/?symbols={clean_sym}&page_size=40"
        res = scraper.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                item_type = item.get("type")
                
                title = ""
                summary = ""
                pub_date = item.get("date") or ""
                date_str = ""
                if pub_date:
                    try:
                        dt = datetime.datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                        date_str = dt.strftime("%d.%m.%Y %H:%M")
                    except Exception:
                        date_str = pub_date[:10] if len(pub_date) >= 10 else pub_date
                        
                link = f"https://fintables.com/sirketler/{clean_sym}/akis"
                source = "Fintables Haber"
                
                if item_type == "post":
                    p = item.get("post") or {}
                    title = item.get("title") or p.get("title") or "Haber"
                    summary = p.get("body") or p.get("excerpt") or ""
                    source = "Fintables Haber"
                elif item_type == "article":
                    art = item.get("article") or {}
                    title = art.get("title") or item.get("title") or "Araştırma Notu"
                    summary = art.get("description") or art.get("excerpt") or ""
                    slug = art.get("slug")
                    if slug:
                        link = f"https://fintables.com/analiz/{slug}"
                    source = "Fintables Araştırma"
                elif item_type in ["news", "disclosure"]:
                    n = item.get("news") or item.get("disclosure") or {}
                    title = item.get("subtitle") or n.get("summary") or n.get("subject") or item.get("title") or "KAP Bildirimi"
                    summary = n.get("note") or n.get("summary") or n.get("subject") or ""
                    kap_id = n.get("kap_id") or n.get("id")
                    if kap_id:
                        link = f"https://www.kap.org.tr/tr/Bildirim/{kap_id}"
                    source = "KAP Bildirimi"
                elif item_type == "newsletter":
                    nl = item.get("newsletter") or {}
                    title = item.get("title") or nl.get("title") or "Bülten"
                    summary = nl.get("description") or nl.get("excerpt") or ""
                    source = "Fintables Bülten"
                else:
                    title = item.get("title") or item.get("subtitle") or ""
                    summary = item.get("summary") or ""
                    
                if title:
                    title_clean = re.sub('<[^<]+?>', '', title).strip()
                    summary_clean = re.sub('<[^<]+?>', '', summary).strip()
                    if title_clean:
                        formatted_news.append({
                            "title": title_clean,
                            "summary": summary_clean,
                            "source": source,
                            "url": link,
                            "date": date_str
                        })
    except Exception as e:
        print(f"Fintables news fetch error for {clean_sym}: {e}")
        
    if formatted_news:
        _news_cache[clean_sym] = {'timestamp': now, 'data': formatted_news}
    else:
        formatted_news = [
            {
                "title": f"{clean_sym} için öne çıkan güncel haber bulunamadı.",
                "summary": "",
                "source": "Sistem",
                "url": f"https://fintables.com/sirketler/{clean_sym}/akis",
                "date": "-"
            }
        ]
        
    return formatted_news

@router.get("/news/{symbol}")
def get_news(symbol: str):
    """
    Fetch featured news and disclosures for a symbol from Fintables feed.
    """
    try:
        news_data = fetch_fintables_news(symbol)
        return {
            "symbol": symbol,
            "news": news_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/broker-targets/{symbol}")
def get_broker_targets(symbol: str):
    """
    Fetch Fintables analyst recommendations summary and detailed broker target prices.
    """
    try:
        clean_symbol = symbol.replace(".IS", "").upper()
        summary, targets = fetch_fintables_summary(clean_symbol)
        
        return {
            "symbol": symbol,
            "summary": summary,
            "targets": targets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug-fintables/{symbol}")
def debug_fintables(symbol: str):
    clean_sym = symbol.replace(".IS", "").upper()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': f'https://fintables.com/sirketler/{clean_sym}/analist-tavsiyeleri',
        'Origin': 'https://fintables.com'
    }
    
    scraper = cloudscraper.create_scraper()
    r1 = scraper.get(f"https://api.fintables.com/analyst-ratings/?code={clean_sym}", headers=headers, timeout=8)
    r2 = scraper.get(f"https://api.fintables.com/topic-feed/?symbols={clean_sym}&page_size=40", headers=headers, timeout=8)
    
    return {
        "symbol": clean_sym,
        "analyst_ratings_status": r1.status_code,
        "analyst_ratings_preview": r1.text[:300],
        "topic_feed_status": r2.status_code,
        "topic_feed_preview": r2.text[:300]
    }


