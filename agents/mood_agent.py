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
    return {"success": True, "mood": mood, "score": entry["score"],
            "avg": round(avg, 1), "trend": trend}


@tool
def get_mood_history_tool(user_id: int) -> dict:
    """Return the last 7 mood entries for the user formatted for display."""
    history = get_mood_history(user_id, days=7)
    avg     = get_rolling_mood_avg(user_id)
    formatted = [
        f"{h['logged_at'][:16].replace('T',' ')} — {h['mood']} ({h['mood_score']}/10)"
        for h in history
    ]
    return {"count": len(history), "avg": round(avg, 1), "entries": formatted}


def make_mood_agent() -> Agent:
    return Agent(
        name="MoodTrackerAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[record_mood, get_mood_history_tool],
        instructions=[
            "You have two tools: record_mood and get_mood_history_tool.",
            "Rule 1: If the message asks for mood history, last mood, recent moods → call get_mood_history_tool.",
            "Rule 2: If the message contains an actual emotion/feeling → infer mood and call record_mood.",
            "Rule 3: If no emotion expressed (e.g. 'track mood') → reply: 'How are you feeling today?'",
            "Valid moods: happy, sad, excited, tired, anxious, calm, irritable, neutral.",
            "Map naturally: stressed→anxious, exhausted→tired, great→happy, depressed→sad.",
            "For history: list each entry on its own line, then show the rolling average.",
            "For logging output:",
            "Line 1: Mood logged as <mood> (<score>/10). Your 7-day rolling average is <avg>/10 — trend is <trend>.",
            "Line 2: A warm one-sentence suggestion based on the mood.",
            "No markdown, no extra sentences.",
        ],
        markdown=False,
    )
