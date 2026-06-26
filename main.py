import os
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        print("Telegram response:", response.status_code, response.text[:500])
        return response.ok
    except Exception as exc:
        print("Telegram exception:", repr(exc))
        return False


def to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", ".").strip())
    except Exception:
        return default


def parse_payload() -> Dict[str, Any]:
    data = request.get_json(silent=True)
    if isinstance(data, dict):
        return data

    raw = request.get_data(as_text=True) or ""
    try:
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return loaded
    except Exception:
        pass

    return {"raw_message": raw}


def normalize_direction(data: Dict[str, Any]) -> str:
    text = " ".join(str(v).lower() for v in data.values())

    buy_words = ["buy", "long", "лонг", "купить", "покупка", "вверх", "up"]
    sell_words = ["sell", "short", "шорт", "продать", "продажа", "продавать", "вниз", "down"]

    if any(w in text for w in buy_words):
        return "buy"
    if any(w in text for w in sell_words):
        return "sell"

    return "watch"


def simple_analysis(data: Dict[str, Any]) -> str:
    symbol = data.get("symbol") or data.get("ticker") or "XAUUSD"
    timeframe = data.get("timeframe") or data.get("interval") or data.get("tf") or "unknown"
    price = to_float(data.get("price") or data.get("close"))
    zone_low = to_float(data.get("zone_low"))
    zone_high = to_float(data.get("zone_high"))

    direction = normalize_direction(data)
    price_text = f"{price:.2f}" if price is not None else str(data.get("price") or data.get("close") or "не указана")

    action = "⏳ ЖДАТЬ"
    direction_text = "Наблюдение"
    probability = 50
    entry = price_text
    sl = "—"
    tp1 = "—"
    tp2 = "—"
    reasons = []

    if direction == "buy":
        action = "✅ ВХОД ВОЗМОЖЕН"
        direction_text = "🟢 LONG / BUY"
        probability = 62
        if price is not None:
            risk = 2.5
            sl = f"{price - risk:.2f}"
            tp1 = f"{price + risk:.2f}"
            tp2 = f"{price + risk * 2:.2f}"
        reasons = [
            "TradingView прислал BUY/LONG сигнал",
            "Проверить закрепление выше уровня",
            "Вход только после подтверждения на M1/M5",
        ]

    elif direction == "sell":
        action = "✅ ВХОД ВОЗМОЖЕН"
        direction_text = "🔴 SHORT / SELL"
        probability = 62
        if price is not None:
            risk = 2.5
            sl = f"{price + risk:.2f}"
            tp1 = f"{price - risk:.2f}"
            tp2 = f"{price - risk * 2:.2f}"
        reasons = [
            "TradingView прислал SELL/SHORT сигнал",
            "Проверить закрепление ниже уровня",
            "Вход только после подтверждения на M1/M5",
        ]

    else:
        reasons = [
            "TradingView прислал уведомление без направления",
            "Это сигнал наблюдения, не автоматический вход",
            "Нужно проверить структуру H1/M15/M5",
        ]

    if zone_low is not None and zone_high is not None and price is not None:
        if zone_low <= price <= zone_high:
            probability -= 10
            reasons.append("Цена внутри зоны — лучше ждать выход")
        elif price > zone_high:
            reasons.append("Цена выше указанной зоны")
        elif price < zone_low:
            reasons.append("Цена ниже указанной зоны")

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    reasons_text = "\n".join(f"• {r}" for r in reasons)
    raw_note = data.get("note") or data.get("message") or data.get("raw_message") or ""

    return f"""⚡ <b>AK Scalping AI v2</b>

<b>Инструмент:</b> {symbol}
<b>ТФ:</b> {timeframe}
<b>Цена:</b> {price_text}

<b>Вход:</b> {action}
<b>Направление:</b> {direction_text}
<b>Точка входа:</b> {entry}
<b>SL:</b> {sl}
<b>TP1:</b> {tp1}
<b>TP2:</b> {tp2}
<b>Вероятность:</b> {probability}%

<b>Причина:</b>
{reasons_text}

<b>Комментарий:</b> {raw_note}
<b>Время:</b> {now_utc}

⚠️ Это учебный помощник. Решение о сделке принимаешь только после проверки графика.
"""


@app.get("/")
def home():
    return "AK Scalping AI v2 is running ✅"


@app.get("/health")
def health():
    return jsonify({"status": "ok", "version": "2.0"})


@app.get("/telegram/test")
@app.post("/telegram/test")
def telegram_test():
    ok = send_telegram("✅ AK Scalping AI v2 подключен. Telegram работает.")
    return jsonify({"sent": ok})


@app.get("/webhook")
def webhook_get():
    return jsonify({
        "status": "webhook is alive",
        "message": "TradingView must send POST requests here",
        "example": {
            "secret": WEBHOOK_SECRET or "optional",
            "symbol": "XAUUSD",
            "timeframe": "M1",
            "close": "4027.00",
            "trend": "buy"
        }
    })


@app.post("/webhook")
def webhook_post():
    data = parse_payload()
    print("Incoming webhook:", json.dumps(data, ensure_ascii=False)[:1500])

    if WEBHOOK_SECRET:
        received_secret = data.get("secret") or request.headers.get("X-AK-SECRET", "")
        if received_secret != WEBHOOK_SECRET:
            print("Bad secret. Received:", received_secret)
            return jsonify({
                "ok": False,
                "error": "bad secret",
                "hint": "Add correct secret field to TradingView message or update WEBHOOK_SECRET in Railway"
            }), 403

    message = simple_analysis(data)
    sent = send_telegram(message)
    return jsonify({"ok": True, "telegram_sent": sent, "received": data})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
