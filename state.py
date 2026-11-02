"""SQLite-backed conversation state.

Tracks which chats are under bait control, how many turns we've sent, and the
message history we feed the LLM. Also records a manual-override flag so that if
*you* ever send a message in a baited chat, the bot permanently backs off.
"""
import json
import sqlite3
import time
from contextlib import contextmanager

import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    user_id     INTEGER PRIMARY KEY,
    status      TEXT NOT NULL DEFAULT 'baiting',  -- baiting | stopped | manual_override
    turns       INTEGER NOT NULL DEFAULT 0,
    history     TEXT NOT NULL DEFAULT '[]',
    created_at  REAL NOT NULL,
    updated_at  REAL NOT NULL
);
"""


@contextmanager
def _conn():
    con = sqlite3.connect(config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init():
    with _conn() as con:
        con.executescript(_SCHEMA)


def get(user_id: int):
    with _conn() as con:
        row = con.execute("SELECT * FROM chats WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def start_baiting(user_id: int):
    now = time.time()
    with _conn() as con:
        con.execute(
            "INSERT OR IGNORE INTO chats(user_id, created_at, updated_at) VALUES(?,?,?)",
            (user_id, now, now),
        )


def append_history(user_id: int, role: str, text: str):
    rec = get(user_id)
    history = json.loads(rec["history"]) if rec else []
    history.append({"role": role, "text": text})
    with _conn() as con:
        con.execute(
            "UPDATE chats SET history=?, updated_at=? WHERE user_id=?",
            (json.dumps(history[-40:]), time.time(), user_id),
        )
    return history


def history(user_id: int) -> list[dict]:
    rec = get(user_id)
    return json.loads(rec["history"]) if rec else []


def bump_turn(user_id: int) -> int:
    with _conn() as con:
        con.execute(
            "UPDATE chats SET turns = turns + 1, updated_at=? WHERE user_id=?",
            (time.time(), user_id),
        )
        row = con.execute("SELECT turns FROM chats WHERE user_id=?", (user_id,)).fetchone()
        return row["turns"] if row else 0


def set_status(user_id: int, status: str):
    with _conn() as con:
        con.execute(
            "INSERT INTO chats(user_id, status, created_at, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET status=excluded.status, updated_at=excluded.updated_at",
            (user_id, status, time.time(), time.time()),
        )


def is_active(user_id: int) -> bool:
    rec = get(user_id)
    return bool(rec) and rec["status"] == "baiting"
