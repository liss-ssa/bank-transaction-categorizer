from app.categorization.rules import categorize_by_rules
from app.data.schemas import Transaction


def tx(description: str, bank_category: str = "Прочее") -> Transaction:
    return Transaction(id="1", date="2026-01-01", description=description, amount=-100, currency="RUB", bank_category=bank_category)


def test_groceries_rule():
    assert categorize_by_rules(tx("OPLATA ZA PRODUKTY LENTA")).predicted_category == "food.groceries"


def test_taxi_rule():
    assert categorize_by_rules(tx("Yandex Go MOSCOW")).predicted_category == "transport.taxi"


def test_unknown_rule():
    assert categorize_by_rules(tx("UNKNOWN MERCHANT 123")).predicted_category == "unknown"
