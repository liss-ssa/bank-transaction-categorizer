from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    id: str
    parent_id: str | None
    ru_name: str
    description: str


CATEGORIES: list[Category] = [
    Category("food.groceries", "food", "Супермаркеты и продукты", "Продуктовые магазины, супермаркеты, доставка продуктов"),
    Category("food.restaurants", "food", "Кафе и рестораны", "Кафе, рестораны, фастфуд, кофейни"),
    Category("transport.taxi", "transport", "Такси", "Такси и райдшеринг"),
    Category("transport.public", "transport", "Общественный транспорт", "Метро, автобусы, транспортные карты"),
    Category("transport.fuel", "transport", "Топливо", "АЗС, бензин, автомойка"),
    Category("health.pharmacy", "health", "Аптеки", "Аптеки, лекарства"),
    Category("health.clinic", "health", "Медицина", "Клиники, стоматология, анализы"),
    Category("home.utilities", "home", "Коммунальные услуги", "ЖКХ, электричество, вода, газ"),
    Category("telecom.mobile_internet", "telecom", "Связь и интернет", "Мобильная связь, интернет-провайдеры"),
    Category("subscriptions.digital", "subscriptions", "Цифровые подписки", "Музыка, фильмы, облака, приложения"),
    Category("shopping.clothes", "shopping", "Одежда и обувь", "Магазины одежды и обуви"),
    Category("shopping.marketplaces", "shopping", "Маркетплейсы", "Маркетплейсы и интернет-магазины"),
    Category("entertainment.cinema", "entertainment", "Кино и события", "Кинотеатры, концерты, билеты"),
    Category("travel.hotels", "travel", "Отели и поездки", "Отели, авиабилеты, жд билеты"),
    Category("finance.cash", "finance", "Снятие наличных", "Банкоматы и cash withdrawal"),
    Category("finance.transfers", "finance", "Переводы", "Переводы физлицам, СБП"),
    Category("finance.fees", "finance", "Комиссии", "Банковские комиссии и обслуживание"),
    Category("other", None, "Прочее", "Только если нельзя уверенно отнести к другой категории"),
    Category("unknown", None, "Без категории", "Нужно ручное рассмотрение или дополнительный контекст"),
]

CATEGORY_IDS = [c.id for c in CATEGORIES]
CATEGORY_BY_ID = {c.id: c for c in CATEGORIES}

TAXONOMY_TEXT = "\n".join(
    f"- {c.id}: {c.ru_name}. {c.description}" for c in CATEGORIES if c.id not in {"unknown"}
)
