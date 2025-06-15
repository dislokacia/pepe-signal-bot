from flask import Flask, request
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

app = Flask(__name__)

TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

def send_to_telegram(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def get_price_binance(symbol="PEPEUSDT"):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
    try:
        response = requests.get(url).json()
        df = pd.DataFrame(response, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_volume", "taker_buy_quote_volume", "ignore"
        ])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        return None

def analyze_macd(df):
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    last_macd = df["macd"].iloc[-1]
    last_signal = df["signal"].iloc[-1]
    if last_macd > last_signal:
        return "🐂 Bullish MACD crossover — возможно, стоит купить PEPE."
    elif last_macd < last_signal:
        return "🐻 Bearish MACD crossover — возможно, стоит продать PEPE."
    else:
        return "⚠️ Нет чёткого сигнала от MACD."

@app.route("/")
def home():
    return "PEPE Signal Bot Running"

@app.route("/report-daily")
def report():
    df = get_price_binance()
    if df is None or df.empty:
        send_to_telegram("⚠️ Не удалось получить данные от Binance.")
        return "No data"
    macd_msg = analyze_macd(df)
    send_to_telegram(f"📊 PEPE анализ:

{macd_msg}")
    return "Sent"

if __name__ == "__main__":
    app.run()
