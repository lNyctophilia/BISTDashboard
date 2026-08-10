import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()
url = 'https://tr.investing.com/equities/turk-hava-yollari-technical'
response = scraper.get(url)
print("Status:", response.status_code)
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the summary text
    summary = soup.find(string=lambda t: t and ("Özet:" in t or "Özet" in t or "Güçlü Al" in t or "Güçlü Sat" in t))
    print(summary)
    
    # Or just look for the technical analysis box
    elements = soup.select('.summary span')
    for el in elements:
        print(el.text)
        
    print(response.text[:500])
else:
    print("Failed to get page.")
