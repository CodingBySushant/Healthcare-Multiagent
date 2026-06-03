"""
Mood Tracker Agent — captures user mood, stores it with a numeric score,
surfaces rolling average and trend clearly in the response.
"""
import os
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from agents.db import log_mood, get_mood_history, get_rolling_mood_avg

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
VALID_MOODS  = ["happy","sad","excited","tired","anxious","calm","irritable","neutral"]


@tool
def record_mood(user_id: int, mood: str) -> dict:
    """Record a mood entry and return score, rolling average, and trend."""
    mood = mood.lower().strip()
    if mood not in VALID_MOODS:
        return {"success": False,
                "message": f"Could not map to a valid mood. Choose from: {', '.join(VALID_MOODS)}."}
    entry   = log_mood(user_id, mood)
    avg     = get_rolling_mood_avg(user_id)
    history = get_mood_history(user_id, days=7)
    trend   = "stable"
    if len(history) >= 3:
        recent = sum(h["mood_score"] for h in history[:3]) / 3
        if recent > avg + 1:   trend = "improving"
        elif recent < avg - 1: trend = "declining"
    return {
        "success": True,
        "mood":    mood,
        "score":   entry["score"],
        "avg":     round(avg, 1),
        "trend":   trend,
    }


def make_mood_agent() -> Agent:
    return Agent(
        name="MoodTrackerAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[record_mood],
        instructions=[
            "Infer the mood from the message (stressed→anxious, exhausted→tired, great→happy).",
            "Call record_mood with user_id and the inferred mood word.",
            "Output EXACTLY two lines:",
            "Line 1: Mood logged as <mood> (<score>/10).",
            "Line 2: Your 7-day rolling average is <avg>/10 — trend is <trend>.",
            "No markdown, no extra sentences.",
        ],
        markdown=False,
    )
