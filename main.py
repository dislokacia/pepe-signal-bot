from flask import Flask
import requests
import pandas as pd

app = Flask(__name__)

BOT_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/pepe/market_chart"

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
    return "✅ PEPE Signal Bot (CoinGecko) is running."

@app.route("/report-daily")
def report():
    try:
        send_message("🔧 Тест: Cron вызвал report-daily, бот работает.")  # отладка

        params = {
            "vs_currency": "usd",
            "days": "1",
            "interval": "minutely"
        }
        r = requests.get(COINGECKO_URL, params=params, timeout=5)
        data = r.json()

        prices = data.get("prices", [])
        if len(prices) < 30:
            return "Недостаточно данных для анализа MACD.", 200

        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["price"] = df["price"].astype(float)

        ema12 = df["price"].ewm(span=12).mean()
        ema26 = df["price"].ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()

        if len(macd) < 3 or len(signal) < 3:
            return "Недостаточно данных для анализа MACD.", 200

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


