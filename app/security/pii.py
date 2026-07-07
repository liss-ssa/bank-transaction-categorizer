from __future__ import annotations

import re

CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
PHONE_RE = re.compile(r"(?:\+7|8)[\s\-()]?\d{3}[\s\-()]?\d{3}[\s\-()]?\d{2}[\s\-()]?\d{2}")


def mask_pii(text: str) -> str:
    text = CARD_RE.sub("[CARD_MASKED]", text)
    text = PHONE_RE.sub("[PHONE_MASKED]", text)
    return text
