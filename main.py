import requests
import pandas as pd
import numpy as np
from flask import Flask, request
import time

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]
SYMBOLS = ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]

BINANCE_URL = "https://api.binance.com/api/v3/klines"

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        requests.post(url, data=payload)

def fetch_binance_data(symbol, interval="15m", limit=100):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(BINANCE_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"])
        df["close"] = pd.to_numeric(df["close"])
        return df
    return None

def calculate_indicators(df):
    df["EMA12"] = df["close"].ewm(span=12).mean()
    df["EMA26"] = df["close"].ewm(span=26).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def analyze_symbol(symbol):
    df = fetch_binance_data(symbol)
    if df is None or df.shape[0] < 30:
        return f"Ошибка анализа {symbol}: недостаточно данных"
    df = calculate_indicators(df)
    price = df["close"].iloc[-1]
    macd = df["MACD"].iloc[-1]
    signal = df["Signal"].iloc[-1]
    rsi = df["RSI"].iloc[-1]

    decision = ""
    if macd > signal and rsi < 70:
        decision = "Покупать (бычий сигнал)"
    elif macd < signal and rsi > 70:
        decision = "Продавать (медвежий сигнал)"
    else:
        decision = "Ждать (неопределенность)"

    return f"📊 Анализ {symbol}:\nЦена: {price:.6f}\nMACD: {macd:.6f}\nSignal: {signal:.6f}\nRSI: {rsi:.2f}\nРешение: {decision}"

@app.route("/report-daily")
def report_daily():
    key = request.args.get("key")
    if key != "pepe_alpha_234":
        return "Invalid key", 403

    messages = []
    for symbol in SYMBOLS:
        try:
            result = analyze_symbol(symbol)
            messages.append(result)
            time.sleep(1.2)  # avoid hitting rate limits
        except Exception as e:
            messages.append(f"Ошибка анализа {symbol}: {str(e)}")

    final_message = "\n\n".join(messages)
    send_to_telegram(f"📰 Ежедневный отчёт:\n\n{final_message}")
    return "Report sent"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
