from flask import Flask, request
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = [6220574513, 788954480]
BINANCE_API_BASE = "https://api.binance.com"


def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")


def get_binance_klines(symbol, interval='1h', limit=100):
    url = f"{BINANCE_API_BASE}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df


def calculate_indicators(df):
    df['EMA_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
    return df


def analyze_symbol(symbol):
    try:
        df = get_binance_klines(symbol, '1h', 100)
        df = calculate_indicators(df)
        price = df['close'].iloc[-1]
        macd = df['MACD'].iloc[-1]
        signal = df['Signal'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        trend = "восходящий" if macd > signal else "нисходящий"

        message = f"📊 Анализ {symbol}:\n"
        message += f"Цена: {price:.6f}\n"
        message += f"MACD: {macd:.6f}, Signal: {signal:.6f} → {trend}\n"
        message += f"RSI: {rsi:.2f}"

        send_to_telegram(message)
        return message
    except Exception as e:
        error_msg = f"❗ Ошибка при анализе {symbol}: {str(e)}"
        send_to_telegram(error_msg)
        return error_msg


@app.route("/report-daily", methods=["GET"])
def report_daily():
    output = []
    for symbol in ["PEPEUSDT", "JTOUSDT", "ETHUSDT", "SOLUSDT"]:
        result = analyze_symbol(symbol)
        output.append(result)
    return "\n".join(output)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
