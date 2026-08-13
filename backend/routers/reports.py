from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
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
            return cached['data']
            
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': f'https://fintables.com/sirketler/{clean_sym}/analist-tavsiyeleri',
        'Origin': 'https://fintables.com'
    }
    
    summary = None
    try:
        url = f"https://api.fintables.com/analyst-ratings/?code={clean_sym}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            targets = [float(x['price_target']) for x in results if x.get('price_target') is not None]
            in_mp = sum(1 for x in results if x.get('in_model_portfolio'))
            
            if targets:
                avg_target = round(sum(targets) / len(targets), 2)
                min_target = round(min(targets), 2)
                max_target = round(max(targets), 2)
                
                current_price = None
                try:
                    time.sleep(random.uniform(0.3, 0.8))
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
        
    if summary is not None:
        _fintables_cache[clean_sym] = {'timestamp': now, 'data': summary}
    return summary






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
        url = f"https://api.fintables.com/topic-feed/?symbols={clean_sym}&page_size=40"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            raw_results = data.get("results", [])
            
            for item in raw_results:
                item_type = item.get("type")
                importance = item.get("importance")
                highlight = item.get("highlight")
                pinned = item.get("pinned")
                
                # Filter for "Öne Çıkanlar" (Featured) news items
                is_featured = (
                    highlight is True or 
                    pinned is True or 
                    importance in ['high', 'mid'] or 
                    item_type in ['post', 'article', 'news']
                )
                
                if not is_featured:
                    continue
                    
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
                    title = item.get("title", "Haber")
                    p = item.get("post") or {}
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
                elif item_type == "news":
                    n = item.get("news") or {}
                    title = item.get("subtitle") or n.get("summary") or n.get("subject") or item.get("title") or "KAP Bildirimi"
                    summary = n.get("note") or n.get("summary") or n.get("subject") or ""
                    kap_id = n.get("kap_id")
                    if kap_id:
                        link = f"https://www.kap.org.tr/tr/Bildirim/{kap_id}"
                    source = "KAP Bildirimi"
                else:
                    title = item.get("title", "")
                    
                if title:
                    formatted_news.append({
                        "title": title,
                        "summary": summary,
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
    Fetch Fintables analyst recommendations summary and consensus target price.
    """
    try:
        clean_symbol = symbol.replace(".IS", "").upper()
        fintables_summary = fetch_fintables_summary(clean_symbol)
        targets = []
        
        # Keep consensus target (from Yahoo Finance or Fintables average)
        try:
            time.sleep(random.uniform(0.3, 0.8))
            yf_symbol = f"{clean_symbol}.IS"
            ticker = yf.Ticker(yf_symbol)
            mean_target = ticker.info.get("targetMeanPrice")
            
            recom_text = "Al"
            recoms = ticker.recommendations
            if recoms is not None and not recoms.empty:
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
            
            target_price_val = round(mean_target, 2) if mean_target else (fintables_summary.get("avg_target_price") if fintables_summary else None)
            
            if target_price_val:
                targets.append({
                    "broker": "Konsensüs (Ortalama)",
                    "target_price": target_price_val,
                    "recommendation": recom_text,
                    "date": "Güncel"
                })
        except Exception as e:
            print(f"Consensus target error: {e}")
            if fintables_summary and fintables_summary.get("avg_target_price"):
                targets.append({
                    "broker": "Konsensüs (Ortalama)",
                    "target_price": fintables_summary["avg_target_price"],
                    "recommendation": "Al",
                    "date": "Güncel"
                })
                
        return {
            "symbol": symbol,
            "summary": fintables_summary,
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
    
    r1 = requests.get(f"https://api.fintables.com/analyst-ratings/?code={clean_sym}", headers=headers, timeout=8)
    r2 = requests.get(f"https://api.fintables.com/topic-feed/?symbols={clean_sym}&page_size=40", headers=headers, timeout=8)
    
    return {
        "symbol": clean_sym,
        "analyst_ratings_status": r1.status_code,
        "analyst_ratings_preview": r1.text[:300],
        "topic_feed_status": r2.status_code,
        "topic_feed_preview": r2.text[:300]
    }


