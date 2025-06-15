
import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import time

app = Flask(__name__)

TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print(f"Ошибка при отправке в Telegram: {e}")

def analyze_token(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=15m&limit=100"
        response = requests.get(url, timeout=10)
        data = response.json()

        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['macd'] = ta.macd(df['close']).iloc[:, 0]
        df['signal'] = ta.macd(df['close']).iloc[:, 1]
        df['rsi'] = ta.rsi(df['close'], length=14)

        macd = df['macd'].iloc[-1]
        signal = df['signal'].iloc[-1]
        rsi = df['rsi'].iloc[-1]
        trend = "бычий" if macd > signal else "медвежий"

        recommendation = "Покупать" if trend == "бычий" and rsi < 70 else "Продавать" if trend == "медвежий" and rsi > 50 else "Держать"

        return f"--- Анализ {symbol} ---\nMACD: {macd:.5f}\nSignal: {signal:.5f}\nRSI: {rsi:.2f}\nТренд: {trend}\nРекомендация: {recommendation}"
    except Exception as e:
        return f"❗ Ошибка при анализе {symbol}: {e}"

@app.route("/report-daily")
def report():
    try:
        pepe = analyze_token("PEPEUSDT")
        jto = analyze_token("JTOUSDT")
        message = pepe + "\n\n" + jto
        send_to_telegram(message)
        return "Отчёт отправлен"
    except Exception as e:
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
