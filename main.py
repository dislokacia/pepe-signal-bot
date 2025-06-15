
import requests
import pandas as pd
from flask import Flask

BOT_TOKEN = "your_bot_token_here"
CHAT_ID_1 = "6220574513"
CHAT_ID_2 = "788954480"

app = Flask(__name__)

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in [CHAT_ID_1, CHAT_ID_2]:
        data = {"chat_id": chat_id, "text": text}
        try:
            r = requests.post(url, data=data, timeout=10)
            print("Telegram:", r.status_code, r.text)
        except Exception as e:
            print("Telegram Error:", str(e))

@app.route("/report-daily")
def report_daily():
    report = "📊 PEPE Отчёт:\n"
    try:
        # Пример расчётов MACD и RSI — здесь должна быть логика анализа
        # Сейчас добавлен только пример:
        price = 0.00001050  # фиктивная цена
        report += f"Цена: {price}\n"

        # Примерное добавление MACD блока
        macd_val = 0.00000012
        sig_val = 0.00000009
        report += f"MACD: {macd_val:.8f}\nСигнал: {sig_val:.8f}\n"

    except Exception as e:
        report += "⚠️ MACD не посчитан\n"
        print("MACD Error:", str(e))

    send_to_telegram(report)
    return "Отправлено"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
