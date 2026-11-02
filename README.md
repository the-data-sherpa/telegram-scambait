# telegram-scambait

A personal **userbot** (MTProto, via Telethon) that watches your own Telegram
DMs, detects first-contact scam/spam from strangers, and strings the scammers
along with LLM-generated bait replies — while leaving every real conversation
completely untouched.

> ⚠️ **Read this first.** This logs in **as your personal account** (not a Bot
> API bot — those can't see your DMs). Automating a personal account is against
> the letter of Telegram's ToS and *can* get an account limited, especially if
> it sends lots of automated replies. Passive detection is low-risk; auto-reply
> (live mode) carries real risk. You accept that risk. Start in `dry_run`.

## How it protects your real chats

- **Whitelist:** contacts and anyone you've *ever sent a message to* are never
  touched.
- **First-contact only:** only brand-new strangers are ever scored.
- **Content scoring:** a stranger needs to trip the spam detector (keywords,
  links, money mentions, bare "hi dear" openers) to get engaged.
- **Manual override:** if *you* type into a baited chat, the bot permanently
  stops for that chat.
- **Caps:** `MAX_BAIT_TURNS` ends each bait thread; replies are rate-limited and
  randomly delayed to look human.
- **Review channel:** everything is mirrored to a private channel you control.

## Setup

1. **Get API credentials:** go to <https://my.telegram.org> → *API development
   tools* → create an app. Note the `api_id` and `api_hash`.

2. **Create a private review channel** in Telegram (just you). You'll put its
   `@username` or numeric id in `REVIEW_CHAT`.

3. **Install** (uses a venv; this box has no system pip):
   ```bash
   cd ~/Projects/telegram-scambait
   python3 -m venv .venv
   source .venv/bin/activate
   python -m ensurepip --upgrade
   pip install -r requirements.txt
   ```

4. **Configure:**
   ```bash
   cp .env.example .env
   # edit .env: TG_API_ID, TG_API_HASH, REVIEW_CHAT, LLM_PROVIDER + key
   # leave MODE=dry_run for now
   ```

5. **First run** (will prompt for your phone + login code once, then saves a
   `.session` file):
   ```bash
   python main.py
   ```

## Going live

Once you've watched `dry_run` logs in your review channel and you're happy it's
only catching real spam (and never real people):

```bash
# in .env
MODE=live
```

Then restart. Begin with a small `MAX_BAIT_TURNS` and a conservative persona.

## Files

| File | Role |
|------|------|
| `main.py` | Telethon event loop: whitelist, detect, bait, manual-override |
| `detector.py` | Rule-based spam scoring of message content |
| `baiter.py` | LLM (Anthropic/OpenAI) or canned bait-reply generation |
| `state.py` | SQLite conversation state + turn/override tracking |
| `config.py` | Env/.env loading + validation |

## Tuning detection

Edit `KEYWORD_PATTERNS` in `detector.py`. The threshold is `points >= 2`
(`Score.is_spam`). Raise it to be more conservative (fewer false positives),
lower it to catch more. Watch the review channel and adjust.

## Kill switch

Stop the process (`Ctrl-C`). Nothing runs when it's not running. To permanently
exclude someone, send them any message yourself (triggers manual override), or
delete/adjust their row in `scambait.db`.
