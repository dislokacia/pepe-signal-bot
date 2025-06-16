import requests
import pandas as pd
import numpy as np
from datetime import datetime

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Получение данных с Binance
def fetch_binance_data(symbol):
    try:
        params = {
            "symbol": symbol,
            "interval": "15m",
            "limit": 100
        }
        response = requests.get(BINANCE_URL, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"])
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"Ошибка запроса {symbol}: {e}")
        return None

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

# Анализ одного актива
def analyze_symbol(symbol):
    df = fetch_binance_data(symbol)
    if df is None or df.shape[0] < 14:
        return f"Ошибка анализа {symbol}: недостаточно данных"

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

    return (f"📊 {symbol}\n"
            f"Цена: {closes.iloc[-1]:.4f}\n"
            f"RSI: {rsi:.2f}\n"
            f"MACD: {macd_val:.4f} | Сигнал: {signal_val:.4f} | Гистограмма: {hist_val:.4f}\n"
            f"EMA12: {ema12:.4f} | EMA26: {ema26:.4f}\n"
            f"Тренд: {trend}\n"
            f"Рекомендация: {recommendation}\n")

# Генерация отчета
def generate_report():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "JTOUSDT", "ADAUSDT", "PEPEUSDT"]
    report = [analyze_symbol(symbol) for symbol in symbols]
    return "\n".join(report)

# Тестовая отправка
if __name__ == "__main__":
    print(generate_report())
