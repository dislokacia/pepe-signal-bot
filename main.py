import requests
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

app = Flask(__name__)

def fetch_pepe_data():
    url = "https://api.binance.com/api/v3/klines?symbol=PEPEUSDT&interval=15m&limit=100"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume", "close_time",
        "quote_asset_volume", "number_of_trades", "taker_buy_base", "taker_buy_quote", "ignore"
    ])
    df["close"] = pd.to_numeric(df["close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
    return df

def calculate_macd(df):
    df["EMA12"] = df["close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    return df

def generate_signal(df):
    if df["MACD"].iloc[-1] > df["Signal"].iloc[-1] and df["MACD"].iloc[-2] <= df["Signal"].iloc[-2]:
        return "🔼 Бычий сигнал (пересечение снизу)"
    elif df["MACD"].iloc[-1] < df["Signal"].iloc[-1] and df["MACD"].iloc[-2] >= df["Signal"].iloc[-2]:
        return "🔽 Медвежий сигнал (пересечение сверху)"
    else:
        return "➖ Сигналов нет"

def send_to_telegram(message):
    url = "https://api.telegram.org/bot<your_token>/sendMessage"
    data = {
        "chat_id": "<your_chat_id>",
        "text": message
    }
    requests.post(url, data=data)

@app.route("/")
def home():
    return "PEPE bot active"

@app.route("/report-daily")
def report():
    try:
        df = fetch_pepe_data()
        if len(df) < 26:
            send_to_telegram("⚠️ Недостаточно данных от Binance для MACD.")
            return "Недостаточно данных"
        df = calculate_macd(df)
        signal = generate_signal(df)
        price = df["close"].iloc[-1]
        send_to_telegram(f"📊 PEPE анализ:
Цена: {price}
MACD: {df['MACD'].iloc[-1]:.8f}
Сигнал: {signal}")


        return "Отчет отправлен"
    except Exception as e:
        send_to_telegram(f"❗ Ошибка в отчете PEPE: {str(e)}")
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
