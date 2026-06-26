# AK Scalping AI v2

TradingView → Railway → Telegram.

## Что изменилось

- `/webhook` отвечает на GET и POST.
- Бот принимает JSON и обычный текст.
- Бот понимает `buy`, `sell`, `long`, `short`, `купить`, `продать`, `лонг`, `шорт`.
- Есть тест Telegram: `/telegram/test`.

## Railway variables

Обязательные:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Опционально:
- `WEBHOOK_SECRET`

Если `WEBHOOK_SECRET` заполнен, в TradingView message добавляйте:

```json
"secret": "ваш_секрет"
```

## TradingView Message BUY

```json
{
  "secret": "AKScalping2026Secret",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "price": "{{close}}",
  "high": "{{high}}",
  "low": "{{low}}",
  "trend": "buy",
  "note": "BUY alert"
}
```

## TradingView Message SELL

```json
{
  "secret": "AKScalping2026Secret",
  "symbol": "{{ticker}}",
  "timeframe": "{{interval}}",
  "price": "{{close}}",
  "high": "{{high}}",
  "low": "{{low}}",
  "trend": "sell",
  "note": "SELL alert"
}
```
