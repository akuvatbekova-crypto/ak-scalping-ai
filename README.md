# AK Scalping AI

Telegram + TradingView webhook assistant for XAUUSD scalping.

## Railway variables

Add these variables in Railway:

- `TELEGRAM_BOT_TOKEN` — token from BotFather
- `TELEGRAM_CHAT_ID` — your Telegram chat id
- `WEBHOOK_SECRET` — any private word, for example `ak2026secret`

## Test endpoints

- `GET /` — health text
- `POST /telegram/test` — sends test message to Telegram
- `POST /webhook` — receives TradingView alert JSON

## TradingView alert JSON example

```json
{
  "secret": "ak2026secret",
  "symbol": "XAUUSD",
  "timeframe": "M5",
  "close": "4041.88",
  "high": "4042.90",
  "low": "4038.14",
  "trend": "buy",
  "zone_low": "4037.00",
  "zone_high": "4040.00",
  "note": "Breakout and retest zone"
}
```

## Important

This bot is an assistant only. It does not guarantee profit and does not open trades automatically.
