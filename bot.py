import os, json, requests

token = os.environ["OANDA_TOKEN"]
account = os.environ["OANDA_ACCOUNT"]
base = f"https://api-fxpractice.oanda.com/v3/accounts/{account}"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
SIZE = "0.1"

# 1. Get gold prices and work out today's signal
r = requests.get(
    "https://api-fxpractice.oanda.com/v3/instruments/XAU_USD/candles",
    headers=headers,
    params={"granularity": "D", "count": 300, "price": "M"},
)
r.raise_for_status()
candles = [c for c in r.json()["candles"] if c["complete"]]
closes = [float(c["mid"]["c"]) for c in candles]
latest = closes[-1]
average = sum(closes[-200:]) / 200
want_gold = latest > average
print(f"Latest close: {latest:.2f} | 200-day average: {average:.2f}")
print("Rule says:", "HOLD GOLD" if want_gold else "STAY IN CASH")

# 2. See what we hold now
r = requests.get(f"{base}/positions/XAU_USD", headers=headers)
r.raise_for_status()
long_units = float(r.json()["position"]["long"]["units"])
print("Currently holding:", long_units, "oz")

# 3. Act
if want_gold and long_units == 0:
    order = {"order": {"type": "MARKET", "instrument": "XAU_USD", "units": SIZE,
                       "timeInForce": "FOK", "positionFill": "DEFAULT"}}
    r = requests.post(f"{base}/orders", headers=headers, data=json.dumps(order))
    print("Bought", SIZE, "oz. Status:", r.status_code)
    if r.status_code not in (200, 201):
        print(r.text)
        raise SystemExit(1)
elif not want_gold and long_units > 0:
    r = requests.put(f"{base}/positions/XAU_USD/close", headers=headers,
                     data=json.dumps({"longUnits": "ALL"}))
    print("Sold. Status:", r.status_code)
    if r.status_code != 200:
        print(r.text)
        raise SystemExit(1)
else:
    print("No change needed.")
