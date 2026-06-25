import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "ak-secret")


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram env vars are missing")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(r.status_code, r.text[:300])
        return r.ok
    except Exception as e:
        print("Telegram error:", e)
        return False


def as_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def analyze_xauusd(data: Dict[str, Any]) -> str:
    """
    First simple AK Scalping logic.
    TradingView can send JSON with: symbol, timeframe, close, high, low, trend, zone_high, zone_low, note.
    Later we will improve rules with your course strategy.
    """
    symbol = data.get("symbol", "XAUUSD")
    tf = data.get("timeframe", data.get("tf", "M1/M5"))
    close = as_float(data.get("close"))
    high = as_float(data.get("high"))
    low = as_float(data.get("low"))
    trend = str(data.get("trend", "unknown")).lower()
    zone_high = as_float(data.get("zone_high"))
    zone_low = as_float(data.get("zone_low"))
    note = data.get("note", "")

    action = "❌ НЕТ"
    direction = "Ждать"
    probability = 45
    entry = "—"
    sl = "—"
    tp1 = "—"
    tp2 = "—"
    reasons = []

    if close is not None and zone_low is not None and zone_high is not None:
        in_zone = zone_low <= close <= zone_high
        above_zone = close > zone_high
        below_zone = close < zone_low

        if trend in ["long", "buy", "up", "bull"] and above_zone:
            action = "✅ ДА"
            direction = "🟢 Лонг"
            probability = 75
            entry = f"{close:.2f} после ретеста"
            sl = f"{zone_low:.2f}"
            tp1 = f"{close + (close - zone_low):.2f}"
            tp2 = f"{close + 2 * (close - zone_low):.2f}"
            reasons = ["Цена выше ключевой зоны", "Тренд по сигналу восходящий", "Нужен ретест перед входом"]
        elif trend in ["short", "sell", "down", "bear"] and below_zone:
            action = "✅ ДА"
            direction = "🔴 Шорт"
            probability = 75
            entry = f"{close:.2f} после ретеста"
            sl = f"{zone_high:.2f}"
            tp1 = f"{close - (zone_high - close):.2f}"
            tp2 = f"{close - 2 * (zone_high - close):.2f}"
            reasons = ["Цена ниже ключевой зоны", "Тренд по сигналу нисходящий", "Нужен ретест перед входом"]
        elif in_zone:
            probability = 40
            reasons = ["Цена внутри зоны", "Нет подтвержденного выхода", "Лучше ждать пробой или отбой"]
        else:
            probability = 55
            reasons = ["Есть движение от зоны", "Но не хватает подтверждения по стратегии"]
    else:
        reasons = ["Недостаточно данных в alert", "Нужны close, zone_low, zone_high и trend"]

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    reasons_text = "\n".join([f"• {r}" for r in reasons])
    return f"""📊 <b>{symbol}</b> | {tf}

<b>Вход:</b> {action}
<b>Направление:</b> {direction}
<b>Точка входа:</b> {entry}
<b>Стоп-лосс:</b> {sl}
<b>TP1:</b> {tp1}
<b>TP2:</b> {tp2}
<b>Вероятность:</b> {probability}%

<b>Причина:</b>
{reasons_text}

<b>Комментарий:</b> {note}
<b>Время:</b> {now}
"""


@app.get("/")
def home():
    return "AK Scalping AI is running ✅"


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/telegram/test")
def telegram_test():
    text = "✅ AK Scalping AI подключен. Telegram работает."
    ok = send_telegram(text)
    return jsonify({"sent": ok})


@app.post("/webhook")
def webhook():
    data = request.get_json(silent=True) or {}
    secret = data.get("secret", request.headers.get("X-AK-SECRET", ""))
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "bad secret"}), 403

    message = analyze_xauusd(data)
    ok = send_telegram(message)
    return jsonify({"ok": ok, "message": message})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
