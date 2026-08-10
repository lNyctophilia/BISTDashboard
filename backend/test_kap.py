import pykap

try:
    comp = pykap.bist.BISTCompany(ticker="THYAO")
    disc2 = comp.get_disclosures()
    print("get_disclosures:", len(disc2))
    if len(disc2) > 0:
        print("sample disc2:", type(disc2[0]), dir(disc2[0]) if not isinstance(disc2[0], dict) else disc2[0].keys())
        print(disc2[0])
except Exception as e:
    print(e)
