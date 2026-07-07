from pydantic import BaseModel, Field, field_validator
from app.categorization.taxonomy import CATEGORY_IDS


class Transaction(BaseModel):
    id: str
    date: str
    description: str = Field(min_length=1, max_length=512)
    amount: float
    currency: str = Field(default="RUB", min_length=3, max_length=3)
    bank_category: str | None = None
    true_category: str | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class CategorizationResult(BaseModel):
    id: str
    predicted_category: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    reason: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @field_validator("predicted_category")
    @classmethod
    def valid_category(cls, value: str) -> str:
        if value not in CATEGORY_IDS:
            raise ValueError(f"Unknown category: {value}")
        return value
