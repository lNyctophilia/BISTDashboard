import requests
from bs4 import BeautifulSoup

h = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/takip-listesi.aspx', headers=h)
soup = BeautifulSoup(r.text, 'html.parser')

tables = soup.find_all('table', class_='excelexport')
for i, t in enumerate(tables):
    print(f"\n--- Table {i} ---")
    headers = [th.text.strip() for th in t.find_all('th')]
    print("Headers:", headers)
    
    rows = t.find('tbody').find_all('tr') if t.find('tbody') else []
    for row in rows[:2]: # print first 2 rows
        cols = [td.text.strip() for td in row.find_all('td')]
        print(cols)
