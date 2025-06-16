import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

COINGECKO_CHART_URL = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"
TELEGRAM_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = ["6220574513", "788954480"]

SYMBOL_TO_COINGECKO_ID = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT": "ethereum",
    "SOLUSDT": "solana",
    "JTOUSDT": "jito",
    "ADAUSDT": "cardano",
    "PEPEUSDT": "pepe"
}

# Получение данных с CoinGecko (hourly)

def fetch_coingecko_data(symbol):
    try:
        coin_id = SYMBOL_TO_COINGECKO_ID.get(symbol)
        if not coin_id:
            raise ValueError("Unknown CoinGecko ID")
        url = COINGECKO_CHART_URL.format(id=coin_id)
        params = {"vs_currency": "usd", "days": "1", "interval": "hourly"}
        response = requests.get(url, params=params)
        data = response.json()
        prices = data.get("prices", [])
        if not prices or len(prices) < 14:
            raise ValueError("Not enough CoinGecko data")
        df = pd.DataFrame(prices, columns=["timestamp", "close"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"Ошибка CoinGecko {symbol}: {e}")
        return generate_dummy_data()

# Запасной вариант — фейковые данные

def generate_dummy_data():
    closes = [2 + 0.01 * np.sin(i / 3.0) for i in range(100)]
    return pd.DataFrame({"close": closes})

# Индикаторы

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_ema(prices, span):
    return prices.ewm(span=span, adjust=False).mean()

def calculate_macd(prices):
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd_line = ema12 - ema26
    signal_line = calculate_ema(macd_line, 9)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

# Анализ одного актива с фильтрацией по RSI

def analyze_symbol(symbol):
    df = fetch_coingecko_data(symbol)
    if df is None or df.shape[0] < 14:
        return None

    closes = df["close"]

    rsi = calculate_rsi(closes).iloc[-1]
    macd, signal, hist = calculate_macd(closes)
    macd_val = macd.iloc[-1]
    signal_val = signal.iloc[-1]
    hist_val = hist.iloc[-1]

    ema12 = calculate_ema(closes, 12).iloc[-1]
    ema26 = calculate_ema(closes, 26).iloc[-1]

    trend = "восходящий" if ema12 > ema26 else "нисходящий"

    recommendation = "Держать"
    if rsi < 35:
        recommendation = "Покупать (перепроданность)"
    elif rsi > 70:
        recommendation = "Фиксировать прибыль (перекупленность)"

    if rsi < 35 or rsi > 70:
        return (f"📊 {symbol}\n"
                f"Цена: {closes.iloc[-1]:.4f}\n"
                f"RSI: {rsi:.2f}\n"
                f"MACD: {macd_val:.4f} | Сигнал: {signal_val:.4f} | Гистограмма: {hist_val:.4f}\n"
                f"EMA12: {ema12:.4f} | EMA26: {ema26:.4f}\n"
                f"Тренд: {trend}\n"
                f"Рекомендация: {recommendation}\n")
    return None

# Генерация отчета только по важным сигналам

def generate_report():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "JTOUSDT", "ADAUSDT", "PEPEUSDT"]
    report = filter(None, [analyze_symbol(symbol) for symbol in symbols])
    return "\n".join(report)

# Отправка в Telegram

def send_telegram_message(message):
    if not message:
        return
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Ошибка Telegram: {e}")

# Тестовая отправка
if __name__ == "__main__":
    report = generate_report()
    print(report)
    send_telegram_message(report)
