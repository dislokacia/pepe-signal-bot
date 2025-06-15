import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import time

app = Flask(__name__)

# Telegram
TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]

def send_to_telegram(message: str):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=data)
        except Exception as e:
            print(f"Ошибка при отправке в Telegram: {e}")

def get_price_from_binance(symbol="PEPEUSDT"):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    response = requests.get(url)
    return float(response.json()["price"])

def get_candles(symbol="PEPEUSDT", interval="15m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close",
                                     "volume", "close_time", "quote_asset_volume",
                                     "number_of_trades", "taker_buy_base_asset_volume",
                                     "taker_buy_quote_asset_volume", "ignore"])
    df["close"] = pd.to_numeric(df["close"])
    return df

@app.route("/report-daily", methods=["GET", "POST"])
def report():
    try:
        df = get_candles()
        if len(df) < 35:
            send_to_telegram("⚠️ Недостаточно данных для анализа PEPE.")
            return "Недостаточно данных"

        df["MACD"] = ta.macd(df["close"])["MACD_12_26_9"]
        df["SIGNAL"] = ta.macd(df["close"])["MACDs_12_26_9"]
        price = get_price_from_binance()

        if df["MACD"].iloc[-1] > df["SIGNAL"].iloc[-1]:
            signal = "Покупать (бычий сигнал)"
        elif df["MACD"].iloc[-1] < df["SIGNAL"].iloc[-1]:
            signal = "Продавать (медвежий сигнал)"
        else:
            signal = "Наблюдать (нет сигнала)"

        send_to_telegram(f"""📊 PEPE Анализ:
Цена: {price}
MACD: {df['MACD'].iloc[-1]:.8f}
Сигнал: {signal}""")
        return "Отчет отправлен"
    except Exception as e:
        send_to_telegram(f"❗ Ошибка в отчете PEPE: {str(e)}")
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
