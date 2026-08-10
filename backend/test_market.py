from routers.market import get_signals
import json

try:
    res = get_signals("THYAO.IS")
    print(json.dumps(res, indent=2))
except Exception as e:
    print(f"Error: {e}")
