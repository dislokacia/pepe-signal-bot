from flask import Flask, request
import requests
import pandas as pd
import pandas_ta as ta
import time

app = Flask(__name__)

TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = [6220574513, 788954480]

BINANCE_API_URL = "https://api.binance.com/api/v3/klines"

def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"Ошибка при отправке в Telegram: {e}")

def get_klines(symbol, interval='15m', limit=100):
    url = f"{BINANCE_API_URL}?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=['time','o','h','l','c','v','ct','qv','n','taker_base_vol','taker_quote_vol','ignore'])
    df['c'] = df['c'].astype(float)
    return df

def analyze_symbol(symbol):
    df = get_klines(symbol)
    df['MACD'] = ta.macd(df['c'])['MACD_12_26_9']
    df['MACD_signal'] = ta.macd(df['c'])['MACDs_12_26_9']
    df['RSI'] = ta.rsi(df['c'])
    df['EMA20'] = ta.ema(df['c'], length=20)

    macd = df['MACD'].iloc[-1]
    signal = df['MACD_signal'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    ema = df['EMA20'].iloc[-1]
    price = df['c'].iloc[-1]

    message = (
        f"📊 Анализ {symbol}:
"
        f"Цена: {price:.6f} USD\n"
        f"MACD: {macd:.6f}, Сигнал: {signal:.6f}\n"
        f"RSI: {rsi:.2f}\n"
        f"EMA (20): {ema:.6f}\n"
    )

    if macd > signal and rsi < 70:
        message += "Рекомендация: 📈 Покупать или держать."
    elif macd < signal and rsi > 70:
        message += "Рекомендация: 📉 Продавать."
    else:
        message += "Рекомендация: ⏸️ Подождать."

    return message

@app.route("/analyze")
def analyze():
    try:
        symbols = ['PEPEUSDT', 'JTOUSDT', 'SOLUSDT', 'ETHUSDT']
        full_message = ""
        for symbol in symbols:
            full_message += analyze_symbol(symbol) + "\n\n"
            time.sleep(1)  # небольшая задержка для API Binance

        send_to_telegram(full_message)
        return "Анализ отправлен"
    except Exception as e:
        send_to_telegram(f"❗ Ошибка анализа: {str(e)}")
        return f"Ошибка: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
