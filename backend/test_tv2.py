import requests
import json
resp = requests.post("https://scanner.tradingview.com/turkey/scan", json={"symbols":{"tickers":["BIST:EREGL"]},"columns":["Recommend.Other","Recommend.All","Recommend.MA"]}, headers={"User-Agent": "Mozilla/5.0"})
print(resp.status_code, resp.text)
