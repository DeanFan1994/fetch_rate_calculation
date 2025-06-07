
from flask import Flask, request, jsonify
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许所有域名访问，也可以只指定你自己的前端地址

def get_binance_rates():
    def get_rate(asset, fiat, trade_type, pay_types, amount_limit):
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        payload = {
            "asset": asset,
            "fiat": fiat,
            "tradeType": trade_type,
            "payTypes": pay_types,
            "page": 1,
            "rows": 20
        }
        headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        r = requests.post(url, headers=headers, json=payload)
        data = r.json()
        rates = []
        for item in data["data"]:
            adv = item["adv"]
            if int(adv["minSingleTransAmount"]) <= amount_limit <= int(adv["maxSingleTransAmount"]):
                rates.append(float(adv["price"]))
        return sum(rates)/len(rates) if rates else None

    xaf_usdt = get_rate("USDT", "XAF", "SELL", ["MTNMOBILEMONEY", "MoMoNew", "MoMo"], 200000) + 3
    usdt_cny = get_rate("USDT", "CNY", "BUY", ["ALIPAY", "WECHAT"], 2000) - 0.04
    my_rate = xaf_usdt / usdt_cny / (1 - 0.015)
    return round(my_rate, 2)

@app.route("/api/exchange-rate", methods=["GET"])
def exchange_rate():
    rate = get_binance_rates()
    return jsonify({"rate": rate})

@app.route("/api/calculate", methods=["POST"])
def calculate():
    data = request.get_json()
    rate = float(data["rate"])
    amount = float(data["amount"])
    type_ = data["type"]

    if type_ == "XAF":
        charges = max(amount * 0.05, 1000)
        exchanged = (amount - charges) / rate
        return jsonify({"result": int(exchanged)})
    elif type_ == "CNY":
        base = amount * rate
        charges = max(base / 0.95 * 0.05, 1000)
        xaf_total = base + charges
        return jsonify({"result": int((xaf_total // 100 + 1) * 100)})
    else:
        return jsonify({"error": "Invalid type"}), 400

if __name__ == "__main__":
    app.run(debug=True)
