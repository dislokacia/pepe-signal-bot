from flask import Flask
import requests
import pandas as pd
import pandas_ta as ta

app = Flask(__name__)

BOT_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

BINANCE_URL = "https://api.binance.com/api/v3/klines"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CryptoBot/1.0; +https://cryptogpt.app)"
}

in_position = False  # Простая переменная состояния

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
    return "✅ RSI+MACD PEPE Bot is running."

@app.route("/report-daily")
def report():
    global in_position
    try:
        params = {"symbol": "PEPEUSDT", "interval": "5m", "limit": 200}
        r = requests.get(BINANCE_URL, params=params, headers=HEADERS, timeout=10)
        data = r.json()

        if isinstance(data, list) and len(data) >= 50:
            df = pd.DataFrame(data, columns=['time','open','high','low','close','volume','c','q','n','t','m','i'])
            df['close'] = df['close'].astype(float)

            # RSI и MACD
            df.ta.rsi(length=10, append=True)
            df.ta.macd(fast=8, slow=21, signal=5, append=True)

            rsi = df['RSI_10'].iloc[-1]
            macd = df['MACD_8_21_5'].iloc[-1]
            signal = df['MACDs_8_21_5'].iloc[-1]
            prev_macd = df['MACD_8_21_5'].iloc[-2]
            prev_signal = df['MACDs_8_21_5'].iloc[-2]

            messages = [f"📊 RSI: {round(rsi, 2)} | MACD: {round(macd, 10)} | Signal: {round(signal, 10)}"]

            if rsi < 30:
                messages.append("⚠️ RSI < 30 — перепроданность. Ждём подтверждения MACD.")
            if prev_macd < prev_signal and macd > signal:
                if not in_position:
                    messages.append("📈 Подтверждение MACD: покупка!")
                    in_position = True
            elif prev_macd > prev_signal and macd < signal:
                if in_position:
                    messages.append("📉 MACD пересёк вниз — продаём.")
                    in_position = False

            send_message("\n".join(messages))
            return "✅ Sent to Telegram", 200
        else:
            send_message("⚠️ Недостаточно данных для анализа RSI+MACD.")
            return "✅ Sent to Telegram", 200
    except Exception as e:
        send_message("❌ Ошибка анализа RSI+MACD.")
        return "✅ Sent to Telegram (ошибка)", 200

app.run(host="0.0.0.0", port=10000)
