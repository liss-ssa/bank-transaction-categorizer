from __future__ import annotations

import asyncio
from collections.abc import Iterable

import pandas as pd
from tqdm import tqdm

from app.categorization.llm_openrouter import OpenRouterClient
from app.categorization.rules import categorize_by_rules
from app.config import settings
from app.data.schemas import CategorizationResult, Transaction
from app.security.rate_limit import AsyncRateLimiter


def read_transactions(path: str) -> list[Transaction]:
    df = pd.read_csv(path)
    required = {"id", "date", "description", "amount", "currency"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return [Transaction(**row.dropna().to_dict()) for _, row in df.iterrows()]


def batch(items: list[Transaction], size: int) -> Iterable[list[Transaction]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


async def categorize_transactions(transactions: list[Transaction]) -> list[CategorizationResult]:
    initial = [categorize_by_rules(tx) for tx in transactions]
    tx_by_id = {tx.id: tx for tx in transactions}
    needs_llm = [
        tx_by_id[r.id]
        for r in initial
        if r.confidence < settings.llm_confidence_threshold or r.predicted_category in {"unknown", "other"}
    ]
    result_by_id = {r.id: r for r in initial}
    if settings.llm_enabled and needs_llm:
        client = OpenRouterClient()
        limiter = AsyncRateLimiter(max_calls=20, period_seconds=60)
        for tx_batch in tqdm(list(batch(needs_llm, settings.llm_batch_size)), desc="LLM fallback"):
            await limiter.wait()
            llm_results = await client.classify_batch(tx_batch)
            for res in llm_results:
                result_by_id[res.id] = res
    return [result_by_id[tx.id] for tx in transactions]


def categorize_file(input_path: str, output_path: str) -> pd.DataFrame:
    transactions = read_transactions(input_path)
    results = asyncio.run(categorize_transactions(transactions))
    tx_df = pd.read_csv(input_path)
    res_df = pd.DataFrame([r.model_dump() for r in results])
    out = tx_df.merge(res_df, on="id", how="left")
    out.to_csv(output_path, index=False)
    return out
