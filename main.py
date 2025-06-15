
from flask import Flask, request
import requests
import pandas as pd
import numpy as np
import time
import datetime
from binance.client import Client

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
TELEGRAM_CHAT_IDS = ["6220574513", "788954480"]

def send_to_telegram(message: str):
    for chat_id in TELEGRAM_CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)

def get_klines(symbol: str, interval: str = "1h", limit: int = 100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    return response.json()

def analyze_symbol(symbol: str):
    try:
        raw_data = get_klines(symbol)
        df = pd.DataFrame(raw_data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "num_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])
        df["close"] = df["close"].astype(float)

        # EMA
        df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()

        # MACD
        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        latest = df.iloc[-1]
        trend = "восходящий 📈" if latest.MACD > latest.Signal else "нисходящий 📉"
        rsi_state = (
            "перекупленность 🔺" if latest.RSI > 70 else
            "перепроданность 🔻" if latest.RSI < 30 else
            "нормальный уровень"
        )

        message = (
            f"📊 Анализ {symbol}:
"
            f"Цена: {latest['close']:.6f}
"
            f"MACD: {latest['MACD']:.6f}, Signal: {latest['Signal']:.6f}
"
            f"RSI: {latest['RSI']:.2f} ({rsi_state})
"
            f"Тренд: {trend}"
        )
        send_to_telegram(message)
    except Exception as e:
        send_to_telegram(f"❗ Ошибка анализа {symbol}: {str(e)}")

@app.route("/report-daily")
def report_daily():
    key = request.args.get("key")
    if key != "pepe_alpha_234":
        return "Unauthorized", 403

    for symbol in ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]:
        analyze_symbol(symbol)

    return "Report sent", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
