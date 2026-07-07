from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

MERCHANTS: dict[str, list[str]] = {
    "food.groceries": ["Пятерочка", "Магнит", "ВкусВилл", "Перекресток", "LENTA", "OPLATA ZA PRODUKTY", "Самокат продукты"],
    "food.restaurants": ["Додо Пицца", "Кофемания", "Burger King", "KFC", "Yandex Eda", "Restoran Vostok", "кофейня у дома"],
    "transport.taxi": ["Yandex Go", "Uber", "Citymobil", "Такси Максим", "OPLATA TAXI"],
    "transport.public": ["Московский транспорт", "Метро", "Тройка", "Автобус", "SPB METRO"],
    "transport.fuel": ["Лукойл", "Газпромнефть", "Shell", "Rosneft AZS", "АЗС трасса"],
    "health.pharmacy": ["Аптека 36.6", "Ригла", "Горздрав", "Apteka", "Farmacia"],
    "health.clinic": ["Инвитро", "Гемотест", "Стоматология", "Клиника Семейная", "MEDSI"],
    "home.utilities": ["ЖКХ", "Мосэнергосбыт", "Квартплата", "Vodokanal", "Газпром межрегионгаз"],
    "telecom.mobile_internet": ["МТС", "Билайн", "Мегафон", "Tele2", "Ростелеком интернет"],
    "subscriptions.digital": ["KINopoisk", "IVI", "Spotify", "Apple.com/bill", "Yandex Plus", "Netflix"],
    "shopping.clothes": ["Zara", "Gloria Jeans", "Lamoda", "Спортмастер", "Ostin"],
    "shopping.marketplaces": ["Ozon", "Wildberries", "AliExpress", "Яндекс Маркет", "Marketplace payment"],
    "entertainment.cinema": ["КиноПоиск билеты", "КАРО", "Формула Кино", "Concert ticket", "Афиша"],
    "travel.hotels": ["РЖД", "Aeroexpress", "Aeroflot", "S7 Airlines", "Booking.com", "Отель Москва"],
    "finance.cash": ["ATM SBERBANK", "Снятие наличных", "Cash withdrawal", "Банкомат ВТБ"],
    "finance.transfers": ["СБП перевод", "Перевод Иванов", "Transfer to card", "Пополнение карты"],
    "finance.fees": ["Комиссия банка", "Service fee", "SMS информирование", "Обслуживание карты"],
}

BANK_MISC_PROB = {
    "food.groceries": 0.08,
    "food.restaurants": 0.10,
    "transport.taxi": 0.15,
    "shopping.marketplaces": 0.20,
    "subscriptions.digital": 0.30,
}

BANK_CATEGORY_MAP = {
    "food.groceries": "Продукты",
    "food.restaurants": "Рестораны",
    "transport.taxi": "Транспорт",
    "transport.public": "Транспорт",
    "transport.fuel": "Авто",
    "health.pharmacy": "Аптеки",
    "health.clinic": "Медицина",
    "home.utilities": "Дом",
    "telecom.mobile_internet": "Связь",
    "subscriptions.digital": "Развлечения",
    "shopping.clothes": "Покупки",
    "shopping.marketplaces": "Покупки",
    "entertainment.cinema": "Развлечения",
    "travel.hotels": "Путешествия",
    "finance.cash": "Наличные",
    "finance.transfers": "Переводы",
    "finance.fees": "Комиссии",
}


def generate_synthetic(n: int, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)
    categories = list(MERCHANTS)
    weights = np.array([10, 7, 4, 3, 3, 4, 2, 3, 4, 3, 3, 7, 2, 2, 2, 5, 1], dtype=float)
    weights = weights / weights.sum()
    start = date.today() - timedelta(days=365)
    rows = []
    for i in range(n):
        cat = str(np.random.choice(categories, p=weights))
        merchant = random.choice(MERCHANTS[cat])
        suffix = random.choice(["", " MOSCOW", " SPB", " *ONLINE", f" #{random.randint(1000,9999)}"])
        description = f"{merchant}{suffix}"
        amount = -round(float(np.random.lognormal(mean=6.2, sigma=0.75)), 2)
        if cat.startswith("finance.transfers"):
            amount = -round(float(np.random.lognormal(mean=7.0, sigma=0.8)), 2)
        if cat == "finance.cash":
            amount = -random.choice([1000, 2000, 3000, 5000, 10000])
        misc_prob = BANK_MISC_PROB.get(cat, 0.04)
        bank_category = "Прочее" if random.random() < misc_prob else BANK_CATEGORY_MAP[cat]
        rows.append(
            {
                "id": str(uuid4()),
                "date": str(start + timedelta(days=random.randint(0, 365))),
                "description": description,
                "amount": amount,
                "currency": "RUB",
                "bank_category": bank_category,
                "true_category": cat,
            }
        )
    return pd.DataFrame(rows)


def save_synthetic(n: int, output: str, seed: int = 42) -> None:
    df = generate_synthetic(n=n, seed=seed)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


if __name__ == "__main__":
    save_synthetic(1000, "data/synthetic/transactions.csv")
