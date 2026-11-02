"""Spam/scam detection.

Deliberately conservative: we only ever want to engage *strangers* who send
unsolicited openers. The whitelist checks (contact, prior interaction) happen in
main.py against the Telegram client; this module scores message *content*.
"""
import re
from dataclasses import dataclass

# High-signal scam phrases (investment / romance / crypto / job / prize)
KEYWORD_PATTERNS = [
    r"\b(crypto|bitcoin|btc|usdt|forex|trading|invest(ment|ing)?)\b",
    r"\b(profit|roi|returns?|double your|passive income)\b",
    r"\b(binance|coinbase|wallet address|seed phrase)\b",
    r"\b(lottery|winner|prize|claim your|congratulations)\b",
    r"\b(work from home|job offer|hiring|earn \$?\d+)\b",
    r"\b(hi dear|hello dear|how are you doing today|i came across your profile)\b",
    r"\b(telegram|whatsapp) (me|group|channel)\b",
    r"\b(gift card|western union|money ?gram)\b",
]

LINK_PATTERN = re.compile(r"(https?://|t\.me/|@\w{5,})", re.IGNORECASE)
MONEY_PATTERN = re.compile(r"[$€£]\s?\d|\d+\s?(usd|usdt|eur|btc)", re.IGNORECASE)
GREETING_ONLY = re.compile(
    r"^\s*(hi|hello|hey|good (morning|day|evening))\b\s*(dear|friend|there)?[\s!,.]*$",
    re.IGNORECASE,
)

_COMPILED = [re.compile(p, re.IGNORECASE) for p in KEYWORD_PATTERNS]


@dataclass
class Score:
    points: int
    reasons: list[str]

    @property
    def is_spam(self) -> bool:
        return self.points >= 2


def score_message(text: str) -> Score:
    """Score a single message's text. >=2 points => treat as spam."""
    text = text or ""
    points = 0
    reasons: list[str] = []

    hits = [p.pattern for p in _COMPILED if p.search(text)]
    if hits:
        points += len(hits)
        reasons.append(f"keywords({len(hits)})")

    if LINK_PATTERN.search(text):
        points += 1
        reasons.append("link/handle")

    if MONEY_PATTERN.search(text):
        points += 1
        reasons.append("money")

    # A bare "hi" as a *first* message from a stranger is the classic opener.
    if GREETING_ONLY.match(text):
        points += 1
        reasons.append("bare-greeting")

    return Score(points=points, reasons=reasons)
