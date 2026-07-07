# Bank Transaction Categorizer MVP

MVP для учебной задачи: улучшить категоризацию банковских транзакций физлица и минимизировать `Прочее`.

## Основные возможности

- генерация синтетических банковских выписок
- rule-based классификация
- словарь известных мерчантов
- подсчёт количества использованных токенов
- offline evaluation
- REST API на FastAPI
- контейнеризация через Docker Compose
- модульная архитектура проекта

## Архитектура

``` text
Transactions
      │
Normalization
      │
Merchant Dictionary
      │
 Rule Engine
      │
confidence?
 ┌────┴─────┐
 │          │
High      Low
 │          │
 │     OpenRouter
 │          │
 └────┬─────┘
      │
Final category
      │
Evaluation
```

## Быстрый старт

``` bash
cp .env.example .env
docker compose up -d --build
```

Swagger:

-   http://localhost:8000/docs

Health:

-   http://localhost:8000/health

Run pipeline:

``` powershell
Invoke-RestMethod -Method Post http://localhost:8000/pipeline/all `
-ContentType "application/json" `
-Body '{"rows":1000,"seed":42,"use_llm":false}'
```

Metrics:

``` powershell
Invoke-RestMethod http://localhost:8000/metrics
```

## Категории

Используется небольшая иерархия:

- `food.groceries`
- `food.restaurants`
- `transport.taxi`
- `transport.public`
- `transport.fuel`
- `health.pharmacy`
- `health.clinic`
- `home.utilities`
- `telecom.mobile_internet`
- `subscriptions.digital`
- `shopping.clothes`
- `shopping.marketplaces`
- `entertainment.cinema`
- `travel.hotels`
- `finance.cash`
- `finance.transfers`
- `finance.fees`
- `other`
- `unknown`

`other` и `unknown` используются только как последний вариант.

## OpenRouter

OpenRouter endpoint: `https://openrouter.ai/api/v1/chat/completions`.
MVP использует structured outputs через `response_format.type=json_schema`, чтобы ответ можно было надежно парсить.

Пример `.env`:

```env
OPENROUTER_API_KEY=...
OPENROUTER_MODEL=openai/gpt-4o-mini
LLM_ENABLED=true
LLM_BATCH_SIZE=20
LLM_CONFIDENCE_THRESHOLD=0.74
```

# Результаты

Датасет: **1000 синтетических транзакций**, seed=42.

## Rules only

  Metric                            Value
  -------------------------- ------------
  Accuracy                      **0.988**
  Macro F1                     **0.9369**
  Unknown                        **1.2%**
  Other                          **0.0%**
  Accuracy on bank "Other"      **96.3%**
  Tokens                                0

## Rules + OpenRouter fallback

  Metric                            Value
  -------------------------- ------------
  Accuracy                      **0.997**
  Macro F1                     **0.9427**
  Unknown                        **0.3%**
  Other                          **0.0%**
  Accuracy on bank "Other"      **96.3%**
  Prompt tokens                    15,732
  Completion tokens                 7,284
  Total tokens                 **23,016**

## Comparison

  Metric        Rules   Rules + LLM
  ---------- -------- -------------
  Accuracy      0.988     **0.997**
  Macro F1     0.9369    **0.9427**
  Unknown        1.2%      **0.3%**
  Tokens            0    **23,016**

## Безопасность

- API ключи только через `.env`; `.env` нельзя коммитить.
- Перед LLM применяется простая маскировка карт и телефонов.
- В Docker включен `no-new-privileges`, контейнер приложения запускается не от root.
- LLM fallback батчируется и имеет rate limiter.
- CSV валидируется через Pydantic-схемы.

## Offline A/B вместо production A/B

Для MVP рекомендуется сравнивать режимы:

1. Rules only: `LLM_ENABLED=false`.
2. Rules + LLM fallback: `LLM_ENABLED=true`.
3. LLM-only можно добавить отдельным экспериментом, но он дороже и менее экономичен.

Главные метрики:

- `accuracy`
- `macro_f1`
- `accuracy_on_bank_misc`
- `predicted_other_on_bank_misc_rate`
- `unknown_rate`
- `total_tokens`

## FastAPI mode

The `app` container now runs as a long-lived FastAPI service instead of exiting after the CLI starts without arguments.

Start services:

```bash
docker compose up -d --build
```

Open API docs:

- http://localhost:8000/docs
- health check: http://localhost:8000/health

Run the full offline pipeline via API:

```bash
curl -X POST http://localhost:8000/pipeline/all \
  -H "Content-Type: application/json" \
  -d '{"rows":1000,"seed":42,"use_llm":false}'
```

Get metrics after the job succeeds:

```bash
curl http://localhost:8000/metrics
```

Individual endpoints:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"rows":1000,"seed":42}'

curl -X POST http://localhost:8000/categorize \
  -H "Content-Type: application/json" \
  -d '{"use_llm":false}'

curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{}'
```

CLI is still available inside the running container:

```bash
docker compose exec app python -m app.main generate --rows 1000
docker compose exec app python -m app.main run --use-llm false
docker compose exec app python -m app.main evaluate
```

PostgreSQL is exposed on host port `5433` to avoid conflicts with local PostgreSQL on `5432`.

## Ограничения

Результаты получены на основе синтетических данных. Для развертывания производства
потребуются обезличенные данные о реальных транзакциях, обогащение торговых сетей,
коды MCC, мониторинг и непрерывная оценка.
