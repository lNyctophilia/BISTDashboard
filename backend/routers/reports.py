from fastapi import APIRouter, HTTPException
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import pykap
import time
import re
import datetime
import io

router = APIRouter()

# Global caches with 1 hour TTL
_ak_cache = {'timestamp': 0, 'data': {}}
_ziraat_cache = {'timestamp': 0, 'data': {}}
_yky_cache = {'timestamp': 0, 'data': {}}
_deniz_cache = {'timestamp': 0, 'data': {}}
_tera_cache = {'timestamp': 0, 'data': {}}
_hsbc_cache = {'timestamp': 0, 'data': {}}

def fetch_ak_targets():
    now = time.time()
    if now - _ak_cache['timestamp'] < 3600 and _ak_cache['data']:
        return _ak_cache['data']
        
    targets = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        ak_api_url = 'https://www.akyatirim.com.tr/umbraco/surface/api/ModelPortfoyView?son_donem=true&gecikmeli_fiyat=true'
        ak_res = requests.get(ak_api_url, headers=headers, timeout=5)
        
        if ak_res.status_code != 200:
            ak_page_res = requests.get('https://www.akyatirim.com.tr/tr/raporlarimiz/model-portfoy', headers=headers, timeout=5)
            if ak_page_res.status_code == 200:
                ak_match = re.search(r'(/umbraco/surface/api/ModelPortfoyView[^\'"\s]*)', ak_page_res.text)
                if ak_match:
                    ak_endpoint = ak_match.group(1)
                    ak_res = requests.get(f'https://www.akyatirim.com.tr{ak_endpoint}', headers=headers, timeout=5)

        if ak_res.status_code == 200:
            ak_data = ak_res.json()
            ak_hisses = []
            if isinstance(ak_data, dict) and 'datas' in ak_data and ak_data['datas']:
                ak_hisses = ak_data['datas'][0].get('hisses', [])
            elif isinstance(ak_data, dict) and 'data' in ak_data:
                ak_hisses = ak_data['data']
            elif isinstance(ak_data, list):
                ak_hisses = ak_data

            for h in ak_hisses:
                sym = (h.get('sembol') or h.get('Symbol') or h.get('symbol') or h.get('Hisse') or h.get('hisse') or '').upper().strip()
                target = h.get('hedef_fiyat') or h.get('HedefFiyat') or h.get('targetPrice')
                entry_date = h.get('portfoy_giris_tarihi') or h.get('PortfoyGirisTarihi') or ''
                if sym and target is not None:
                    try:
                        target_val = float(target)
                        if target_val > 0:
                            dt_str = str(entry_date).split('T')[0] if 'T' in str(entry_date) else str(entry_date)
                            targets[sym] = {
                                "broker": "Ak Yatırım",
                                "target_price": round(target_val, 2),
                                "recommendation": "Al",
                                "date": dt_str if dt_str else "Güncel"
                            }
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        print(f"Ak Yatirim scrape error: {e}")

    if targets:
        _ak_cache['timestamp'] = now
        _ak_cache['data'] = targets

    return _ak_cache['data']


def fetch_ziraat_targets():
    now = time.time()
    if now - _ziraat_cache['timestamp'] < 3600 and _ziraat_cache['data']:
        return _ziraat_cache['data']
        
    targets = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    categories = ['39328', '39327']  # 39328: Öneri Portföyü / Raporlar, 39327: Haftalık Teknik Öneriler
    
    for cat_id in categories:
        try:
            payload = {
                'BeginDate': '2020-01-01',
                'EndDate': '2030-01-01',
                'Page': 1,
                'PageSize': 5,
                'SearchTerm': None,
                'CategoryId': cat_id,
                'CheckSubCategory': 'False'
            }
            res = requests.post('https://www.ziraatyatirim.com.tr/umbraco/api/ClockworkUploaderPublic/GetFilesByFilter', json=payload, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                pdf_links = []
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.lower().endswith('.pdf'):
                        if not href.startswith('http'):
                            href = f'https://www.ziraatyatirim.com.tr{href}'
                        pdf_links.append(href)
                
                for pdf_url in pdf_links[:2]:
                    pdf_res = requests.get(pdf_url, headers=headers, timeout=6)
                    if pdf_res.status_code == 200:
                        import pdfplumber
                        with pdfplumber.open(io.BytesIO(pdf_res.content)) as pdf:
                            full_text = ''
                            for page in pdf.pages:
                                full_text += (page.extract_text() or '') + '\n'
                            
                            for line in full_text.splitlines():
                                match = re.search(r'\b([A-Z]{4,5})\b\s+(\d{1,2}\.\d{2}\.\d{4})\b.*?\b(AL|EKLE|TUT|SAT)\b\s+([\d\.\,]+)', line, re.IGNORECASE)
                                if match:
                                    sym, date_str, rec, price_str = match.groups()
                                    s_upper = sym.upper().strip()
                                    if s_upper not in targets:
                                        try:
                                            price = float(price_str.replace('.', '').replace(',', '.'))
                                            targets[s_upper] = {
                                                'broker': 'Ziraat Yatırım',
                                                'target_price': round(price, 2),
                                                'recommendation': rec.strip().capitalize(),
                                                'date': date_str
                                            }
                                        except (ValueError, TypeError):
                                            pass
                if targets:
                    break
        except Exception as e:
            print(f"Ziraat Yatirim scrape error (cat {cat_id}): {e}")

    if targets:
        _ziraat_cache['timestamp'] = now
        _ziraat_cache['data'] = targets

    return _ziraat_cache['data']


def fetch_yky_targets():
    now = time.time()
    if now - _yky_cache['timestamp'] < 3600 and _yky_cache['data']:
        return _yky_cache['data']

    targets = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        url = 'https://www.ykyatirim.com.tr/DetailPage/GetModelPortfolio'
        res = requests.get(url, headers=headers, timeout=5)
        
        # Fallback if URL changes
        if res.status_code != 200:
            page_res = requests.get('https://www.ykyatirim.com.tr/hizmetler/arastirma/model-portfoy-hisse-senedi-onerileri', headers=headers, timeout=5)
            if page_res.status_code == 200:
                match = re.search(r'fetch\(["\'](/DetailPage/GetModelPortfolio[^"\'\s]*)["\']\)', page_res.text)
                if match:
                    endpoint = match.group(1)
                    res = requests.get(f'https://www.ykyatirim.com.tr{endpoint}', headers=headers, timeout=5)

        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list):
                for item in data:
                    sym = (item.get('instrument') or item.get('label') or '').upper().strip()
                    target = item.get('targetPrice')
                    p_date = item.get('proposeDate') or ''
                    if sym and target is not None:
                        try:
                            target_val = float(target)
                            if target_val > 0:
                                dt_str = str(p_date).split('T')[0] if 'T' in str(p_date) else str(p_date)
                                targets[sym] = {
                                    "broker": "Yapı Kredi Yatırım",
                                    "target_price": round(target_val, 2),
                                    "recommendation": "Al",
                                    "date": dt_str if dt_str else "Güncel"
                                }
                        except (ValueError, TypeError):
                            pass
    except Exception as e:
        print(f"Yapi Kredi Yatirim scrape error: {e}")

    if targets:
        _yky_cache['timestamp'] = now
        _yky_cache['data'] = targets

    return _yky_cache['data']


def fetch_deniz_targets():
    now = time.time()
    if now - _deniz_cache['timestamp'] < 3600 and _deniz_cache['data']:
        return _deniz_cache['data']

    targets = {}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9'
    }
    try:
        url = 'https://www.denizyatirim.com/ModelPortfoyPerformans'
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            text = soup.get_text()
            matches = re.findall(r'([A-Z]{4,5})(\d+\.\d{2})(\d+%)', text)
            for sym, price_str, pot in matches:
                if sym not in ['BIST', 'EURO', 'EUR', 'USD', 'MP', 'BIST100']:
                    try:
                        price = float(price_str)
                        targets[sym] = {
                            "broker": "Deniz Yatırım",
                            "target_price": round(price, 2),
                            "recommendation": "Al",
                            "date": "Güncel"
                        }
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        print(f"Deniz Yatirim scrape error: {e}")

    if targets:
        _deniz_cache['timestamp'] = now
        _deniz_cache['data'] = targets

    return _deniz_cache['data']


def fetch_tera_targets():
    now = time.time()
    if now - _tera_cache['timestamp'] < 3600 and _tera_cache['data']:
        return _tera_cache['data']

    targets = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        # Step 1: Get index page to find the latest dated report
        index_url = 'https://www.terayatirim.com/arastirma/oneri-listemiz'
        res = requests.get(index_url, headers=headers, timeout=5)
        latest_report_url = None
        report_date_str = 'Güncel'
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/arastirma/oneri-listemiz/' in href:
                    if not href.startswith('http'):
                        href = 'https://www.terayatirim.com/' + href.lstrip('./')
                    latest_report_url = href
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', href)
                    if date_match:
                        report_date_str = date_match.group(1)
                    break
        
        if not latest_report_url:
            latest_report_url = 'https://www.terayatirim.com/arastirma/oneri-listemiz'

        # Step 2: Get latest report page to find PDF link
        pdf_url = 'https://www.terayatirim.com/dosyalar/arastirma/Model_Portfoey.pdf'
        r_page = requests.get(latest_report_url, headers=headers, timeout=5)
        if r_page.status_code == 200:
            soup_p = BeautifulSoup(r_page.text, 'html.parser')
            for a in soup_p.find_all('a', href=True):
                href = a['href']
                if href.lower().endswith('.pdf') and 'arastirma' in href.lower():
                    if not href.startswith('http'):
                        href = 'https://www.terayatirim.com/' + href.lstrip('./')
                    pdf_url = href
                    break

        # Step 3: Download and parse PDF
        r_pdf = requests.get(pdf_url, headers=headers, timeout=8)
        if r_pdf.status_code == 200:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(r_pdf.content)) as pdf:
                for page in pdf.pages:
                    words = page.extract_words()
                    rows = {}
                    for w in words:
                        top_key = round(w['top'] / 3) * 3
                        rows.setdefault(top_key, []).append(w['text'])
                    
                    for k in sorted(rows.keys()):
                        raw_line = ''.join(''.join(rows[k]).split())
                        match = re.search(r'^([A-Z]{4,5}).*?(\d+,\d{2})(\d+,\d{2})(\d+,\d)%$', raw_line)
                        if match:
                            sym, last_p, target_p, pot = match.groups()
                            try:
                                target = float(target_p.replace(',', '.'))
                                pot_clean = pot.replace(',', '.')
                                targets[sym] = {
                                    'broker': 'Tera Yatırım',
                                    'target_price': round(target, 2),
                                    'recommendation': 'Al',
                                    'date': report_date_str
                                }
                            except (ValueError, TypeError):
                                pass
    except Exception as e:
        print(f"Tera Yatirim scrape error: {e}")

    if targets:
        _tera_cache['timestamp'] = now
        _tera_cache['data'] = targets

    return _tera_cache['data']


def fetch_hsbc_targets():
    now = time.time()
    if now - _hsbc_cache['timestamp'] < 3600 and _hsbc_cache['data']:
        return _hsbc_cache['data']

    targets = {}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        url = 'https://api.fintables.com/analyst-ratings/?brokerage_id=HSY'
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            results = data.get('results', [])
            for item in results:
                sym = (item.get('code') or '').upper().strip()
                price_target = item.get('price_target')
                rec_type = (item.get('type') or 'al').strip().capitalize()
                pub_date = item.get('published_at') or ''
                in_mp = item.get('in_model_portfolio', False)

                if sym and price_target is not None:
                    try:
                        target_val = float(price_target)
                        if target_val > 0 and sym not in targets:
                            dt_str = pub_date.split('T')[0] if 'T' in pub_date else str(pub_date)
                            rec_str = rec_type
                            targets[sym] = {
                                "broker": "HSBC Yatırım",
                                "target_price": round(target_val, 2),
                                "recommendation": rec_str,
                                "date": dt_str if dt_str else "Güncel"
                            }
                    except (ValueError, TypeError):
                        pass
    except Exception as e:
        print(f"HSBC Yatirim scrape error: {e}")

    if targets:
        _hsbc_cache['timestamp'] = now
        _hsbc_cache['data'] = targets

    return _hsbc_cache['data']






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

def is_within_last_days(date_str: str, days: int = 4) -> bool:
    if not date_str or date_str == '-':
        return False
    try:
        parts = date_str.strip().split(' ')
        d_parts = parts[0].split('.')
        if len(d_parts) == 3:
            day = int(d_parts[0])
            month = int(d_parts[1])
            year = int(d_parts[2])
            pub_date = datetime.date(year, month, day)
            today = datetime.date.today()
            return (today - pub_date).days <= days
    except Exception:
        pass
    return False

@router.get("/kap/{symbol}")
def get_kap_reports(symbol: str):
    """
    Fetch and filter recent KAP disclosures for the symbol into 5 key categories:
    Özel Durum Açıklaması, Finansal Rapor, Sermaye Artırımı, Pay Geri Alım, Temettü.
    """
    try:
        clean_symbol = symbol.replace(".IS", "").upper()
        reports = []
        
        try:
            comp = pykap.bist.BISTCompany(ticker=clean_symbol)
            c_id = comp.company_id
            
            today = datetime.date.today()
            from_date = today - datetime.timedelta(days=180)
            
            payload = {
                'fromDate': str(from_date),
                'toDate': str(today),
                'mkkMemberOidList': [c_id],
                'inactiveMkkMemberOidList': [],
                'bdkMemberOidList': [],
                'fromSrc': False,
                'disclosureIndexList': []
            }
            
            res = requests.post('https://www.kap.org.tr/tr/api/disclosure/members/byCriteria', json=payload, timeout=8)
            if res.status_code == 200:
                items = res.json()
                
                def classify_item(item):
                    d_class = item.get('disclosureClass', '')
                    d_type = item.get('disclosureType', '')
                    text = f"{item.get('title') or ''} {item.get('summary') or ''}".lower()
                    
                    if any(k in text for k in ['sermaye art', 'bedelsiz', 'bedelli', 'sermaye azalt', 'hak kullanım']):
                        return 'Sermaye Artırımı'
                    if any(k in text for k in ['geri alım', 'geri alim', 'payların geri', 'pay geri']):
                        return 'Pay Geri Alım'
                    if any(k in text for k in ['kâr dağıtım', 'kar dagit', 'temettü', 'temettu']):
                        return 'Temettü / Kâr Dağıtımı'
                    if d_class == 'FR':
                        return 'Finansal Rapor'
                    if d_class == 'ODA' or d_type == 'ODA':
                        return 'Özel Durum Açıklaması'
                    return None  # Filter out noise (devre kesici, tescil vb.)

                for item in items:
                    category = classify_item(item)
                    if category:
                        disc_idx = item.get('disclosureIndex', '')
                        link = f"https://www.kap.org.tr/tr/Bildirim/{disc_idx}" if disc_idx else "https://www.kap.org.tr/tr/"
                        title = item.get('title') or item.get('summary') or 'KAP Bildirimi'
                        date = item.get('publishDate', '')
                        is_recent = is_within_last_days(date, 4)
                        
                        reports.append({
                            "category": category,
                            "title": title,
                            "summary": item.get('summary', ''),
                            "date": date,
                            "link": link,
                            "is_recent": is_recent
                        })
                        if len(reports) >= 40:  # Return top 40 filtered disclosures
                            break

        except Exception as e:
            print(f"KAP fetch error for {clean_symbol}: {e}")

        # Fallback to pykap basic disclosures if byCriteria returned nothing
        if not reports:
            try:
                comp = pykap.bist.BISTCompany(ticker=clean_symbol)
                disclosures = comp.get_disclosures()
                for item in disclosures[:10]:
                    title = item.get('title', item.get('summary', 'KAP Bildirimi'))
                    date = item.get('publishDate', '')
                    index = item.get('disclosureIndex', '')
                    link = f"https://www.kap.org.tr/tr/Bildirim/{index}" if index else "https://www.kap.org.tr/tr/"
                    is_recent = is_within_last_days(date, 4)
                    reports.append({
                        "category": "Finansal Rapor",
                        "title": title,
                        "date": date,
                        "link": link,
                        "is_recent": is_recent
                    })
            except Exception as e:
                print(f"Pykap fallback error for {clean_symbol}: {e}")

        if not reports:
            reports = [
                {"category": "Bilgi", "title": f"{clean_symbol} için filtrelenmiş KAP bildirimi bulunamadı.", "date": "-", "link": "https://www.kap.org.tr/tr/", "is_recent": True}
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
    Scrape broker target prices from Is Yatirim, Ak Yatirim, Ziraat Yatirim, and Yahoo Finance.
    """
    try:
        clean_symbol = symbol.replace(".IS", "").upper()
        targets = []
        
        # 1. Scrape Is Yatirim from Sirket Karti
        try:
            h = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            r = requests.get(f'https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/sirket-karti.aspx?hisse={clean_symbol}', headers=h, timeout=8)
            if r.status_code == 200:
                r.encoding = 'utf-8'
                soup = BeautifulSoup(r.text, 'html.parser')
                
                hedef_fiyat = 0.0
                oneri = "-"
                tarih = "-"
                
                oneri_span = soup.find('span', id='Oneri_Aciklama')
                if oneri_span:
                    oneri = oneri_span.text.strip().capitalize()
                    
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
                            
                if hedef_fiyat > 0.0:
                    targets.append({
                        "broker": "İş Yatırım", 
                        "target_price": hedef_fiyat, 
                        "recommendation": oneri, 
                        "date": tarih
                    })
        except Exception as e:
            print(f"Is Yatirim scrape error: {e}")

        # 2. Scrape Ak Yatırım Model Portföy
        try:
            ak_targets = fetch_ak_targets()
            if clean_symbol in ak_targets:
                targets.append(ak_targets[clean_symbol])
        except Exception as e:
            print(f"Ak Yatirim target error: {e}")

        # 3. Scrape Yapı Kredi Yatırım Model Portföy
        try:
            yky_targets = fetch_yky_targets()
            if clean_symbol in yky_targets:
                targets.append(yky_targets[clean_symbol])
        except Exception as e:
            print(f"Yapi Kredi Yatirim target error: {e}")

        # 4. Scrape Ziraat Yatırım (Haftalık Teknik / Öneri Portföyü)
        try:
            ziraat_targets = fetch_ziraat_targets()
            if clean_symbol in ziraat_targets:
                targets.append(ziraat_targets[clean_symbol])
        except Exception as e:
            print(f"Ziraat Yatirim target error: {e}")

        # 5. Scrape Deniz Yatırım Model Portföy
        try:
            deniz_targets = fetch_deniz_targets()
            if clean_symbol in deniz_targets:
                targets.append(deniz_targets[clean_symbol])
        except Exception as e:
            print(f"Deniz Yatirim target error: {e}")

        # 6. Scrape Tera Yatırım Model Portföy
        try:
            tera_targets = fetch_tera_targets()
            if clean_symbol in tera_targets:
                targets.append(tera_targets[clean_symbol])
        except Exception as e:
            print(f"Tera Yatirim target error: {e}")

        # 7. Scrape HSBC Yatırım (via Fintables API)
        try:
            hsbc_targets = fetch_hsbc_targets()
            if clean_symbol in hsbc_targets:
                targets.append(hsbc_targets[clean_symbol])
        except Exception as e:
            print(f"HSBC Yatirim target error: {e}")

        # 8. Get Yahoo Finance Consensus
        try:
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
            
            if mean_target:
                targets.append({
                    "broker": "Konsensüs (Ortalama)",
                    "target_price": round(mean_target, 2),
                    "recommendation": recom_text,
                    "date": "Güncel"
                })
                
        except Exception as e:
            print(f"YFinance target error: {e}")
            
        return {
            "symbol": symbol,
            "targets": targets
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

