import requests
import pandas as pd
from flask import Flask
import datetime

app = Flask(__name__)

TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]


def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=data)


def fetch_binance_data():
    url = "https://api.binance.com/api/v3/klines?symbol=PEPEUSDT&interval=5m&limit=100"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"])
        df["close"] = df["close"].astype(float)
        return df["close"]
    else:
        return None


def calculate_macd(close_prices):
    exp1 = close_prices.ewm(span=12, adjust=False).mean()
    exp2 = close_prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd, signal


@app.route("/report-daily")
def report():
    close_prices = fetch_binance_data()
    if close_prices is None or len(close_prices) < 35:
        send_to_telegram("⚠️ Недостаточно данных от Binance для MACD.")
        return "Insufficient data", 200

    macd, signal = calculate_macd(close_prices)
    latest_macd = macd.iloc[-1]
    latest_signal = signal.iloc[-1]

    if latest_macd > latest_signal:
        trend = "🟢 *MACD сигнал на покупку*"
    else:
        trend = "🔴 *MACD сигнал на продажу*"

    message = f"📊 PEPE анализ:\n\nMACD: `{latest_macd:.6f}`\nSignal: `{latest_signal:.6f}`\n\n{trend}"
    send_to_telegram(message)
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
