"""
Shared database utilities for all agents.
Provides typed helpers so agents never write raw SQL.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "/app/data/healthcare.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ── Users ────────────────────────────────────────────────────────────────────

def get_user(user_id: int) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["conditions"] = json.loads(d["conditions"])
        return d


def user_exists(user_id: int) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
        return row is not None


def find_user_by_name(name: str) -> Optional[dict]:
    """Search by first name (case-insensitive). Returns first match or None."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE LOWER(first_name) = LOWER(?)", (name.strip(),)
        ).fetchone()
        if not row:
            # Try partial match
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(first_name) LIKE LOWER(?)",
                (f"{name.strip()}%",)
            ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["conditions"] = json.loads(d["conditions"])
        return d


# ── Mood log ─────────────────────────────────────────────────────────────────

MOOD_SCORES = {
    "happy": 8, "excited": 9, "calm": 7, "neutral": 5,
    "tired": 3, "sad": 2, "anxious": 4, "irritable": 3,
}

def log_mood(user_id: int, mood: str) -> dict:
    score = MOOD_SCORES.get(mood.lower(), 5)
    logged_at = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO mood_log (user_id, mood, mood_score, logged_at) VALUES (?,?,?,?)",
            (user_id, mood, score, logged_at)
        )
    return {"mood": mood, "score": score, "logged_at": logged_at}


def get_mood_history(user_id: int, days: int = 7) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT mood, mood_score, logged_at FROM mood_log
            WHERE user_id = ?
            ORDER BY logged_at DESC
            LIMIT ?
        """, (user_id, days * 3)).fetchall()
        return [dict(r) for r in rows]


def get_rolling_mood_avg(user_id: int) -> float:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT AVG(mood_score) as avg FROM mood_log
            WHERE user_id = ?
        """, (user_id,)).fetchone()
        return round(row["avg"] or 5.0, 2)


# ── CGM log ──────────────────────────────────────────────────────────────────

def log_cgm(user_id: int, reading: int) -> dict:
    flagged = 1 if reading < 80 or reading > 300 else 0
    logged_at = datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cgm_log (user_id, reading, flagged, logged_at) VALUES (?,?,?,?)",
            (user_id, reading, flagged, logged_at)
        )
    return {"reading": reading, "flagged": bool(flagged), "logged_at": logged_at}


def get_cgm_history(user_id: int, limit: int = 21) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT reading, flagged, logged_at FROM cgm_log
            WHERE user_id = ?
            ORDER BY logged_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


def get_latest_cgm(user_id: int) -> Optional[int]:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT reading FROM cgm_log WHERE user_id = ?
            ORDER BY logged_at DESC LIMIT 1
        """, (user_id,)).fetchone()
        return row["reading"] if row else None


# ── Food log ─────────────────────────────────────────────────────────────────

def log_food(user_id: int, description: str, logged_at: Optional[str] = None,
             carbs_g: Optional[float] = None, protein_g: Optional[float] = None,
             fat_g: Optional[float] = None) -> dict:
    ts = logged_at or datetime.now().isoformat()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO food_log (user_id, description, carbs_g, protein_g, fat_g, logged_at)
            VALUES (?,?,?,?,?,?)
        """, (user_id, description, carbs_g, protein_g, fat_g, ts))
    return {
        "description": description,
        "carbs_g": carbs_g,
        "protein_g": protein_g,
        "fat_g": fat_g,
        "logged_at": ts,
    }


def get_food_history(user_id: int, limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT description, carbs_g, protein_g, fat_g, logged_at FROM food_log
            WHERE user_id = ?
            ORDER BY logged_at DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]


# ── Session state ─────────────────────────────────────────────────────────────

def set_session_flow(user_id: int, flow: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO session_state (user_id, active_flow, last_active_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET active_flow=excluded.active_flow,
                last_active_at=excluded.last_active_at
        """, (user_id, flow, datetime.now().isoformat()))


def get_session_flow(user_id: int) -> str:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT active_flow FROM session_state WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["active_flow"] if row else "main"
