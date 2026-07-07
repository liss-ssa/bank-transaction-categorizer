from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.categorization.taxonomy import CATEGORY_IDS, TAXONOMY_TEXT
from app.config import settings
from app.data.schemas import CategorizationResult, Transaction
from app.security.pii import mask_pii


JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORY_IDS},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "reason": {"type": "string"},
                },
                "required": ["id", "category", "confidence", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


class OpenRouterClient:
    def __init__(self) -> None:
        if not settings.openrouter_api_key and settings.llm_enabled:
            raise RuntimeError("OPENROUTER_API_KEY is required when LLM_ENABLED=true")
        self.url = f"{settings.openrouter_base_url.rstrip('/')}/chat/completions"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def classify_batch(self, transactions: list[Transaction]) -> list[CategorizationResult]:
        tx_payload = [
            {
                "id": t.id,
                "description": mask_pii(t.description),
                "amount": t.amount,
                "currency": t.currency,
                "bank_category": t.bank_category,
            }
            for t in transactions
        ]
        system = (
            "Ты классификатор банковских операций физического лица. "
            "Верни только JSON по схеме. Не используй категорию other, если есть правдоподобная специальная категория. "
            "unknown ставь только если недостаточно контекста. Категории:\n" + TAXONOMY_TEXT
        )
        user = "Классифицируй операции:\n" + json.dumps(tx_payload, ensure_ascii=False)
        body = {
            "model": settings.openrouter_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0,
            "max_completion_tokens": 2000,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "transaction_categories", "strict": True, "schema": JSON_SCHEMA},
            },
            "provider": {"require_parameters": True},
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": settings.openrouter_referer,
            "X-Title": settings.openrouter_app_title,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content) if isinstance(content, str) else content
        usage = data.get("usage") or {}
        by_id = {item["id"]: item for item in parsed["items"]}
        results = []
        for t in transactions:
            item = by_id.get(t.id)
            if not item:
                results.append(
                    CategorizationResult(
                        id=t.id,
                        predicted_category="unknown",
                        confidence=0.0,
                        source="llm",
                        reason="missing item in LLM response",
                    )
                )
                continue
            results.append(
                CategorizationResult(
                    id=t.id,
                    predicted_category=item["category"],
                    confidence=float(item["confidence"]),
                    source="llm",
                    reason=item["reason"][:500],
                    prompt_tokens=int(usage.get("prompt_tokens", 0)),
                    completion_tokens=int(usage.get("completion_tokens", 0)),
                    total_tokens=int(usage.get("total_tokens", 0)),
                )
            )
        return results
