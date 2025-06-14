from flask import Flask
import requests
import pandas as pd

app = Flask(__name__)

BOT_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

BINANCE_URL = "https://api.binance.com/api/v3/klines"

def send_message(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        try:
            requests.post(url, data=data, timeout=5)
        except:
            pass

@app.route("/")
def home():
    return "✅ PEPE Signal Bot (Binance) is running."

@app.route("/report-daily")
def report():
    try:
        params = {"symbol": "PEPEUSDT", "interval": "15m", "limit": 100}
        r = requests.get(BINANCE_URL, params=params, timeout=5)
        data = r.json()

        if not isinstance(data, list) or len(data) < 30:
            msg = "⚠️ Недостаточно данных от Binance для MACD."
            send_message(msg)
            return msg, 200

        df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', '_', '_', '_', '_', '_', '_'])
        df['close'] = df['close'].astype(float)

        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()

        if len(macd) < 3 or len(signal) < 3:
            msg = "⚠️ MACD/Signal слишком короткие. Нет возможности сравнить значения."
            send_message(msg)
            return msg, 200

        last_macd = macd.iloc[-1]
        last_signal = signal.iloc[-1]
        prev_macd = macd.iloc[-2]
        prev_signal = signal.iloc[-2]

        macd_val = round(last_macd, 10)
        signal_val = round(last_signal, 10)

        if prev_macd < prev_signal and last_macd > last_signal:
            decision = f"📈 MACD: {macd_val} выше сигнальной {signal_val} → Пересечение вверх. Сигнал на покупку PEPE."
        else:
            decision = f"📊 MACD: {macd_val}, Сигнальная: {signal_val} → Пока без сигнала."

        send_message(decision)
        return decision

    except Exception as e:
        error_msg = f"Ошибка: {str(e)}"
        send_message(error_msg)
        return error_msg, 500

app.run(host="0.0.0.0", port=10000)
