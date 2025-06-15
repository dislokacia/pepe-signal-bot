import requests
import pandas as pd
import pandas_ta as ta
from flask import Flask
import datetime

app = Flask(__name__)

TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        requests.post(url, data=payload)

def get_pepe_price():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=PEPEUSDT"
    r = requests.get(url, headers=HEADERS)
    return float(r.json()['price'])

def get_pepe_candles():
    url = "https://api.binance.com/api/v3/klines?symbol=PEPEUSDT&interval=15m&limit=100"
    r = requests.get(url, headers=HEADERS)
    df = pd.DataFrame(r.json(), columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    return df

@app.route("/report-daily")
def report():
    try:
        df = get_pepe_candles()
        df.ta.macd(close='close', append=True)
        price = get_pepe_price()
        macd = df["MACD_12_26_9"].iloc[-1]
        signal = df["MACDs_12_26_9"].iloc[-1]
        histogram = df["MACDh_12_26_9"].iloc[-1]
        trend = "📈 Покупка" if macd > signal else "📉 Продажа"

        send_to_telegram(
            f"📊 PEPE Анализ:
"
            f"Цена: {price:.8f}
"
            f"MACD: {macd:.8f}
"
            f"Сигнал: {signal:.8f}
"
            f"Гистограмма: {histogram:.8f}
"
            f"Рекомендация: {trend}"
        )
        return "Отчет отправлен"
    except Exception as e:
        send_to_telegram(f"❗ Ошибка: {str(e)}")
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
