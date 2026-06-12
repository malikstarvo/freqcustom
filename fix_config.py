import json
with open("/home/ubuntu/freqtrade/config.json") as f:
    c = json.load(f)
c.setdefault("freqai", {}).setdefault("feature_parameters", {})["feature_columns"] = [
    "ema20", "ema50", "ema200", "rsi14", "atr14", "adx14",
    "volume_ema20", "volatility14",
    "funding_rate", "oi_delta_1_pct", "ls_ratio", "liq_long_usd", "liq_short_usd"
]
with open("/home/ubuntu/freqtrade/config.json", "w") as f:
    json.dump(c, f, indent=4)
print("OK")
