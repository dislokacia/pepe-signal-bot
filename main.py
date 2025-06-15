
import requests
import pandas as pd
from flask import Flask
from datetime import datetime

app = Flask(__name__)

TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["788954480", "6220574513"]

def send_to_telegram(text):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        requests.post(url, data=data)

def fetch_data():
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": "PEPEUSDT",
        "interval": "15m",
        "limit": 100
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

def calculate_macd(df):
    df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = df["ema12"] - df["ema26"]
    df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    return df

@app.route("/report-daily")
def report():
    df = fetch_data()
    if df is None or len(df) < 26:
        return "Недостаточно данных от Binance для MACD."
    df = calculate_macd(df)
    last = df.iloc[-1]
    macd = last["macd"]
    signal = last["signal"]
    trend = "🟢 *ПОКУПАТЬ*" if macd > signal else "🔴 *ПРОДАВАТЬ*"
    send_to_telegram(f"""📊 PEPE анализ:

MACD: `{macd:.8f}`
Signal: `{signal:.8f}`
Тренд: {trend}
""")
    return "Сообщение отправлено"

if __name__ == "__main__":
    app.run()
