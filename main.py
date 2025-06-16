import requests
import pandas as pd
import numpy as np
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]

symbol_mapping = {
    "PEPEUSDT": "pepe",
    "JTOUSDT": "jito",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana"
}

def fetch_binance_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=100"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "close_time", "quote_asset_volume", "number_of_trades", "taker_buy_base", "taker_buy_quote", "ignore"])
        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

def fetch_coingecko(symbol):
    coin = symbol_mapping.get(symbol)
    if not coin:
        return None
    url = f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=1&interval=hourly"
    try:
        resp = requests.get(url).json()
        prices = resp.get("prices", [])
        df = pd.DataFrame(prices, columns=["timestamp", "close"])
        df["close"] = df["close"].astype(float)
        return df
    except:
        return None

def calculate_indicators(df):
    df["EMA"] = df["close"].ewm(span=20, adjust=False).mean()
    df["MACD"] = df["close"].ewm(span=12, adjust=False).mean() - df["close"].ewm(span=26, adjust=False).mean()
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def analyze_symbol(symbol):
    df = fetch_binance_data(symbol)
    if df is None or df.empty:
        df = fetch_coingecko(symbol)
        if df is None or df.empty:
            return f"Ошибка анализа {symbol}: недостаточно данных"

    try:
        df = calculate_indicators(df)
        rsi = df["RSI"].iloc[-1]
        macd = df["MACD"].iloc[-1]
        signal = df["Signal"].iloc[-1]
        ema = df["EMA"].iloc[-1]
        price = df["close"].iloc[-1]

        macd_trend = "бычий" if macd > signal else "медвежий"
        rsi_status = "перекупленность" if rsi > 70 else "перепроданность" if rsi < 30 else "нейтрально"

        recommendation = "покупать" if macd > signal and rsi < 70 else "продавать" if macd < signal and rsi > 70 else "наблюдать"

        return f"📊 Анализ {symbol} (цена: {price:.6f})\nMACD: {macd:.4f} ({macd_trend})\nRSI: {rsi:.2f} ({rsi_status})\nEMA: {ema:.4f}\nРекомендация: {recommendation}"
    except Exception as e:
        return f"Ошибка анализа {symbol}: {str(e)}"

def send_to_telegram(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, data=payload)

@app.route("/report-daily")
def report_daily():
    symbols = ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]
    messages = []
    for symbol in symbols:
        result = analyze_symbol(symbol)
        messages.append(result)
    full_report = "\n\n".join(messages)
    send_to_telegram("📰 Ежедневный отчёт:\n\n" + full_report)
    return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
