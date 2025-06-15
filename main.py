
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
from datetime import datetime
import os

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]
BINANCE_URL = "https://api.binance.com/api/v3/klines"

def fetch_klines(symbol, interval="1h", limit=100):
    try:
        url = f"{BINANCE_URL}?symbol={symbol}&interval={interval}&limit={limit}"
        response = requests.get(url)
        data = response.json()
        if not isinstance(data, list):
            return None
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume", "", "", "", "", "", ""])
        df["close"] = pd.to_numeric(df["close"])
        return df
    except Exception as e:
        print(f"Ошибка загрузки {symbol}: {str(e)}")
        return None

def calculate_indicators(df):
    df["EMA"] = ta.ema(df["close"], length=20)
    macd = ta.macd(df["close"])
    df["MACD"] = macd["MACD_12_26_9"]
    df["MACD_signal"] = macd["MACDs_12_26_9"]
    df["RSI"] = ta.rsi(df["close"], length=14)
    return df

def analyze_symbol(symbol):
    df = fetch_klines(symbol)
    if df is None or df.empty or len(df) < 26:
        return f"{symbol}: Ошибка анализа — недостаточно данных"
    try:
        df = calculate_indicators(df)
        last = df.iloc[-1]
        recommendation = ""
        if last["RSI"] < 30:
            recommendation = "📉 Перепроданность — возможен отскок. Рассмотреть покупку."
        elif last["RSI"] > 70:
            recommendation = "📈 Перекупленность — возможно снижение. Осторожно с покупками."
        elif last["MACD"] > last["MACD_signal"]:
            recommendation = "🟢 MACD бычий кросс — сигнал к покупке."
        else:
            recommendation = "🔴 MACD медвежий кросс — сигнал к продаже или удержанию."
        return (
            f"📊 Анализ {symbol}:
"
            f"Цена: {last['close']:.6f}
"
            f"RSI: {last['RSI']:.2f}
"
            f"MACD: {last['MACD']:.6f}
"
            f"MACD Signal: {last['MACD_signal']:.6f}
"
            f"{recommendation}"
        )
    except Exception as e:
        return f"{symbol}: Ошибка анализа — {str(e)}"

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": message})

@app.route("/report-daily")
def report():
    coins = ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]
    report = ["📰 Ежедневный отчёт:
"]
    for coin in coins:
        report.append(analyze_symbol(coin))
    final_report = "

".join(report)
    send_to_telegram(final_report)
    return "Отчёт отправлен"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
