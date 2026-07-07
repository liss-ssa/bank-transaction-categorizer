from __future__ import annotations

import re
from dataclasses import dataclass

from app.data.schemas import CategorizationResult, Transaction


@dataclass(frozen=True)
class Rule:
    pattern: str
    category: str
    confidence: float
    reason: str


RULES: list[Rule] = [
    Rule(r"пятероч|магнит|вкусвилл|перекрест|lenta|produ[ck]t|самокат", "food.groceries", 0.95, "merchant grocery keyword"),
    Rule(r"додо|кофе|kfc|burger|restoran|yandex eda|ресторан|пицц", "food.restaurants", 0.94, "restaurant keyword"),
    Rule(r"taxi|такси|yandex go|uber|citymobil", "transport.taxi", 0.96, "taxi keyword"),
    Rule(r"метро|тройка|автобус|transport|spb metro", "transport.public", 0.93, "public transport keyword"),
    Rule(r"лукойл|газпромнефть|rosneft|shell|\bазс\b", "transport.fuel", 0.95, "fuel keyword"),
    Rule(r"аптек|apteka|farmacia|ригла|горздрав", "health.pharmacy", 0.96, "pharmacy keyword"),
    Rule(r"инвитро|гемотест|стомат|клиник|medsi", "health.clinic", 0.94, "clinic keyword"),
    Rule(r"жкх|квартплат|энергосбыт|vodokanal|газпром межрегионгаз", "home.utilities", 0.95, "utility keyword"),
    Rule(r"мтс|билайн|мегафон|tele2|ростелеком|internet", "telecom.mobile_internet", 0.92, "telecom keyword"),
    Rule(r"spotify|apple\.com/bill|netflix|ivi|yandex plus|kinopoisk", "subscriptions.digital", 0.91, "subscription keyword"),
    Rule(r"zara|lamoda|gloria|ostin|спортмастер", "shopping.clothes", 0.91, "clothes keyword"),
    Rule(r"ozon|wildberries|aliexpress|маркет|marketplace", "shopping.marketplaces", 0.90, "marketplace keyword"),
    Rule(r"кино|каро|формула кино|concert|афиша", "entertainment.cinema", 0.91, "entertainment keyword"),
    Rule(r"ржд|aeroexpress|aeroflot|s7|booking|отель", "travel.hotels", 0.92, "travel keyword"),
    Rule(r"atm|банкомат|снятие налич|cash withdrawal", "finance.cash", 0.98, "cash withdrawal keyword"),
    Rule(r"сбп|перевод|transfer to card|пополнение карты", "finance.transfers", 0.90, "transfer keyword"),
    Rule(r"комисси|service fee|sms информ|обслуживание карты", "finance.fees", 0.96, "fee keyword"),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("ё", "е")).strip()


def categorize_by_rules(tx: Transaction) -> CategorizationResult:
    text = normalize(f"{tx.description} {tx.bank_category or ''}")
    for rule in RULES:
        if re.search(rule.pattern, text, flags=re.IGNORECASE):
            return CategorizationResult(
                id=tx.id,
                predicted_category=rule.category,
                confidence=rule.confidence,
                source="rules",
                reason=rule.reason,
            )
    return CategorizationResult(
        id=tx.id,
        predicted_category="unknown",
        confidence=0.25,
        source="rules",
        reason="no confident rule matched",
    )
