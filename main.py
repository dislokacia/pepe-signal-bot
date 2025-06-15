
import requests
import pandas as pd
from flask import Flask
from datetime import datetime
import time

app = Flask(__name__)

BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHAT_IDS = ["CHAT_ID_1", "CHAT_ID_2"]

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

@app.route("/report-daily", methods=["GET", "POST"])
def report():
    try:
        df = pd.read_json("https://api.binance.com/api/v3/klines?symbol=PEPEUSDT&interval=5m&limit=100")
        if df.empty or len(df) < 26:
            return "⚠️ Недостаточно данных для анализа."

        df.columns = ['timestamp','open','high','low','close','volume','close_time',
                      'quote_asset_volume','num_trades','taker_buy_base_asset_volume',
                      'taker_buy_quote_asset_volume','ignore']
        df['close'] = df['close'].astype(float)

        short_ema = df['close'].ewm(span=12, adjust=False).mean()
        long_ema = df['close'].ewm(span=26, adjust=False).mean()
        macd = short_ema - long_ema
        signal = macd.ewm(span=9, adjust=False).mean()

        last_macd = macd.iloc[-1]
        last_signal = signal.iloc[-1]
        direction = "покупать" if last_macd > last_signal else "продавать"

        send_to_telegram(f"📊 PEPE анализ:
MACD: {last_macd:.6f}, Сигнальная: {last_signal:.6f}
Рекомендация: *{direction.upper()}*")

        return "✅ Отчёт отправлен."
    except Exception as e:
        return f"❌ Ошибка: {e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
