import requests
import pandas as pd
from flask import Flask, request
from datetime import datetime, timedelta

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]

symbols = ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]


def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        requests.post(url, data=payload)


def fetch_binance_klines(symbol, interval="1h", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "close_time", "qav", "num_trades", "taker_base_vol", "taker_quote_vol", "ignore"])
    df["close"] = pd.to_numeric(df["close"])
    return df


def calculate_indicators(df):
    df["EMA_12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["EMA_26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA_12"] - df["EMA_26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def analyze(symbol):
    df = fetch_binance_klines(symbol)
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    price = latest["close"]
    macd = latest["MACD"]
    signal = latest["Signal"]
    rsi = latest["RSI"]
    trend = "🔼 бычий" if macd > signal else ("🔽 неопределенный" if abs(macd - signal) < 0.01 else "🔽 медвежий")

    recommendation = "💼 Покупать" if rsi < 30 else ("🔓 Продавать" if rsi > 70 else "🤚 Держать")

    return f"\n\n📊 {symbol}\nЦена: {price:.6f}\nMACD: {macd:.6f}, Сигнал: {signal:.6f}\nRSI: {rsi:.2f}\nТренд: {trend}\nРекомендация: {recommendation}"


@app.route("/report-daily")
def report():
    key = request.args.get("key")
    if key != "pepe_alpha_234":
        return "Unauthorized", 401

    report_message = "📰 Ежедневный отчёт:"
    for symbol in symbols:
        try:
            report_message += analyze(symbol)
        except Exception as e:
            report_message += f"\n\n{symbol}: Ошибка анализа — {str(e)}"

    send_to_telegram(report_message)
    return "Report sent"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
