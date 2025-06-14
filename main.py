from flask import Flask
import requests
import pandas as pd

app = Flask(__name__)

BOT_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

BINANCE_URL = "https://api.binance.com/api/v3/klines"
COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/pepe/market_chart"

def send_message(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": text}
        try:
            requests.post(url, data=data, timeout=5)
        except:
            pass

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

@app.route("/")
def home():
    return "✅ PEPE Hybrid Signal Bot is running."

@app.route("/report-daily")
def report():
    try:
        # 1. Пытаемся взять с Binance
        params = {"symbol": "PEPEUSDT", "interval": "5m", "limit": 200}
        r = requests.get(BINANCE_URL, params=params, timeout=5)
        data = r.json()

        if isinstance(data, list) and len(data) >= 30:
            df = pd.DataFrame(data, columns=['time', 'open', 'high', 'low', 'close', 'volume', '_', '_', '_', '_', '_', '_'])
            df['close'] = df['close'].astype(float)

            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()

            last_macd = macd.iloc[-1]
            last_signal = signal.iloc[-1]
            prev_macd = macd.iloc[-2]
            prev_signal = signal.iloc[-2]

            macd_val = round(last_macd, 10)
            signal_val = round(last_signal, 10)

            if prev_macd < prev_signal and last_macd > last_signal:
                decision = f"📈 MACD: {macd_val} > сигнальной {signal_val} → Сигнал на покупку."
            else:
                decision = f"📊 MACD: {macd_val}, Сигнальная: {signal_val} → Пока без сигнала."
        else:
            raise ValueError("Недостаточно данных Binance")

    except:
        # 2. Fallback на CoinGecko + RSI
        try:
            cg_params = {"vs_currency": "usd", "days": "1", "interval": "hourly"}
            r = requests.get(COINGECKO_URL, params=cg_params, timeout=5)
            data = r.json().get("prices", [])

            if len(data) < 20:
                send_message("⚠️ Недостаточно данных от CoinGecko и Binance для анализа.")
                return "✅ Sent to Telegram", 200

            df = pd.DataFrame(data, columns=["time", "price"])
            df["price"] = df["price"].astype(float)
            df["rsi"] = calculate_rsi(df["price"])

            last_rsi = round(df["rsi"].iloc[-1], 2)

            if last_rsi < 30:
                decision = f"🟢 RSI: {last_rsi} — перепроданность. Возможен отскок вверх."
            elif last_rsi > 70:
                decision = f"🔴 RSI: {last_rsi} — перекупленность. Возможна коррекция."
            else:
                decision = f"🟡 RSI: {last_rsi} — нейтральная зона. Сигналов нет."

        except Exception as e:
            send_message("❌ Ошибка получения данных.")
            return "✅ Sent to Telegram (с ошибкой)", 200

    send_message(decision)
    return "✅ Sent to Telegram", 200

app.run(host="0.0.0.0", port=10000)
