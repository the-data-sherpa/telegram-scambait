"""Telegram scambait userbot.

Watches your personal DMs, detects first-contact spam/scam from strangers, and
(in live mode) strings them along with LLM-generated bait replies — while
leaving every real conversation completely untouched.

SAFETY DESIGN
  * Only strangers are ever considered: contacts and anyone you've messaged
    before are hard-whitelisted.
  * If *you* manually send a message into a baited chat, the bot permanently
    backs off that chat (manual override).
  * dry_run mode logs what it *would* do without sending anything. Start there.
  * All activity is mirrored to a review channel if REVIEW_CHAT is set.
"""
import asyncio
import random

from telethon import TelegramClient, events
from telethon.tl.types import User

import baiter
import config
import detector
import state

# Created in main() so the module stays importable without credentials.
client: TelegramClient | None = None

# Cache of user_ids we've confirmed are whitelisted (contact or prior chat).
_whitelist_cache: set[int] = set()
_me_id: int | None = None


async def log_review(text: str):
    if not config.REVIEW_CHAT:
        print(text)
        return
    try:
        await client.send_message(config.REVIEW_CHAT, text)
    except Exception as exc:
        print(f"[review] could not log to REVIEW_CHAT: {exc}\n{text}")


async def is_whitelisted(user: User) -> bool:
    """A sender is safe if they're a contact or we've ever sent them a message."""
    if user.id in _whitelist_cache:
        return True
    if getattr(user, "contact", False) or getattr(user, "mutual_contact", False):
        _whitelist_cache.add(user.id)
        return True
    # Have we ever sent an outgoing message in this chat?
    async for msg in client.iter_messages(user.id, limit=50):
        if msg.out:
            _whitelist_cache.add(user.id)
            return True
    return False


async def send_bait(user_id: int):
    """Generate and (maybe) send one bait reply, with human-ish delay."""
    hist = state.history(user_id)
    reply = baiter.generate_reply(hist)

    delay = config.MIN_REPLY_DELAY + random.randint(0, config.MIN_REPLY_DELAY)
    await asyncio.sleep(delay)

    if config.MODE == "live":
        async with client.action(user_id, "typing"):
            await asyncio.sleep(random.uniform(2, 5))
        await client.send_message(user_id, reply)
        state.append_history(user_id, "me", reply)
        turns = state.bump_turn(user_id)
        await log_review(f"🤖 BAIT→{user_id} (turn {turns}): {reply}")
        if turns >= config.MAX_BAIT_TURNS:
            state.set_status(user_id, "stopped")
            await log_review(f"🛑 Reached MAX_BAIT_TURNS for {user_id}, stopping.")
    else:
        await log_review(f"🧪 [dry_run] would reply to {user_id}: {reply}")


async def on_incoming(event):
    if not event.is_private:
        return
    sender = await event.get_sender()
    if not isinstance(sender, User) or sender.bot or sender.id == _me_id:
        return

    uid = sender.id
    text = event.raw_text or ""

    # Already engaged? Keep the conversation going.
    if state.get(uid):
        if not state.is_active(uid):
            return  # stopped or manual_override
        state.append_history(uid, "scammer", text)
        await send_bait(uid)
        return

    # New sender: never touch whitelisted people.
    if await is_whitelisted(sender):
        return

    score = detector.score_message(text)
    if not score.is_spam:
        return

    name = sender.username or sender.first_name or str(uid)
    state.start_baiting(uid)
    state.append_history(uid, "scammer", text)
    await log_review(
        f"🎯 New suspected scam from {name} ({uid}) "
        f"[{score.points}pts: {', '.join(score.reasons)}]\n   “{text[:200]}”"
    )
    await send_bait(uid)


async def on_outgoing(event):
    """If you reply by hand in a baited chat, back off permanently."""
    if not event.is_private:
        return
    peer = await event.get_chat()
    if isinstance(peer, User) and state.is_active(peer.id):
        state.set_status(peer.id, "manual_override")
        await log_review(
            f"✋ Manual message detected in {peer.id} — bot backing off this chat."
        )


async def main():
    problems = config.validate()
    if problems:
        print("Config problems:")
        for p in problems:
            print(f"  - {p}")
        return

    global client
    client = TelegramClient(config.SESSION_NAME, config.API_ID, config.API_HASH)
    client.add_event_handler(on_incoming, events.NewMessage(incoming=True))
    client.add_event_handler(on_outgoing, events.NewMessage(outgoing=True))

    state.init()
    await client.start(phone=config.PHONE)
    global _me_id
    me = await client.get_me()
    _me_id = me.id

    banner = (
        f"✅ Scambait userbot running as {me.username or me.first_name} ({me.id})\n"
        f"   MODE={config.MODE}  LLM={config.LLM_PROVIDER}  "
        f"max_turns={config.MAX_BAIT_TURNS}"
    )
    print(banner)
    await log_review(banner)
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
