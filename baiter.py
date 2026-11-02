"""Generates time-wasting bait replies in the configured persona.

Providers: anthropic, openai, or 'canned' (no API key needed).
"""
import random

import config

_SYSTEM = (
    "You are roleplaying as {persona}. You are chatting with a scammer who is "
    "trying to defraud you. Your ONLY goal is to waste their time: stay engaged, "
    "seem interested and plausible, but never actually send money, gift cards, "
    "crypto, codes, personal info, or click links. Ask innocent clarifying "
    "questions, misunderstand instructions, invent small harmless delays "
    "('my grandson usually helps me with this'), and keep them talking. "
    "Keep replies short (1-3 sentences), casual, with occasional typos. "
    "Never reveal you are an AI or that you know it's a scam."
)

_CANNED = [
    "Oh interesting! Sorry, how does this work again?",
    "That sounds good but my phone is acting up today. Can you explain once more?",
    "Okay. My grandson usually helps me with these things, he's back tonight.",
    "Wait, which app did you say I need? I get confused with all of them.",
    "How much did you say I could make? That seems like a lot!",
    "Sorry for the slow reply, I was making tea. What do I do first?",
    "I don't think I have that. Is there another way?",
    "Can you send a photo of yourself so I know who I'm talking to?",
]


def _render_system() -> str:
    return _SYSTEM.format(persona=config.BAIT_PERSONA)


def _history_to_text(history: list[dict]) -> str:
    lines = []
    for turn in history[-12:]:
        who = "Scammer" if turn["role"] == "scammer" else "You"
        lines.append(f"{who}: {turn['text']}")
    return "\n".join(lines)


def _anthropic_reply(history: list[dict]) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msgs = [
        {
            "role": "assistant" if t["role"] == "me" else "user",
            "content": t["text"],
        }
        for t in history[-12:]
    ]
    if not msgs or msgs[0]["role"] != "user":
        msgs.insert(0, {"role": "user", "content": "(they messaged you)"})
    resp = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=150,
        system=_render_system(),
        messages=msgs,
    )
    return resp.content[0].text.strip()


def _openai_reply(history: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=config.OPENAI_API_KEY)
    msgs = [{"role": "system", "content": _render_system()}]
    for t in history[-12:]:
        msgs.append(
            {
                "role": "assistant" if t["role"] == "me" else "user",
                "content": t["text"],
            }
        )
    resp = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        max_tokens=150,
        messages=msgs,
    )
    return resp.choices[0].message.content.strip()


def generate_reply(history: list[dict]) -> str:
    """history = [{'role': 'scammer'|'me', 'text': str}, ...] oldest-first."""
    try:
        if config.LLM_PROVIDER == "anthropic":
            return _anthropic_reply(history)
        if config.LLM_PROVIDER == "openai":
            return _openai_reply(history)
    except Exception as exc:  # fall back rather than crash the userbot
        print(f"[baiter] LLM error, using canned reply: {exc}")
    return random.choice(_CANNED)
