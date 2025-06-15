from flask import Flask, request
import requests

app = Flask(__name__)

BOT_TOKEN = "7648757274:AAFtd6ZSR8woBGkcQ7NBOPE559zHwdH65Cw"
CHAT_IDS = [6220574513, 788954480]  # Твои два Telegram чата


def send_to_telegram(message):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": chat_id, "text": message}
        requests.post(url, data=data)


@app.route("/report-daily")
def report_daily():
    key = request.args.get("key")
    if key != "pepe_alpha_234":
        return "Unauthorized", 403

    send_to_telegram("✅ Тестовое сообщение: хук работает!")
    return "Test report sent"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
