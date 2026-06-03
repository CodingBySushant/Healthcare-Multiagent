"""
CGM Agent — validates glucose readings (80–300 mg/dL as per spec),
logs entries, and returns history on request.
"""
import os
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from agents.db import log_cgm, get_cgm_history, get_latest_cgm

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

CGM_LOW, CGM_HIGH = 80, 300


def _classify(r):
    if r < CGM_LOW:   return "critically low — consume fast-acting carbs immediately"
    if r < 90:        return "below target — have a small carb snack"
    if r <= 180:      return "in target range"
    if r <= CGM_HIGH: return "above target — try light activity and avoid high-GI foods"
    return "critically high — consult your doctor immediately"


@tool
def log_glucose_reading(user_id: int, reading: int) -> dict:
    """
    Log a glucose reading. Valid range per spec: 80–300 mg/dL.
    Flags alert if outside this range.
    """
    alert = reading < CGM_LOW or reading > CGM_HIGH
    if reading < 0 or reading > 600:
        return {"success": False, "message": f"{reading} is not a valid glucose value."}
    entry = log_cgm(user_id, reading)
    return {
        "success": True,
        "reading": reading,
        "status": _classify(reading),
        "alert": alert,
        "alert_message": f"⚠️ Reading {reading} mg/dL is outside the safe range (80–300)." if alert else "",
    }


@tool
def fetch_glucose_history(user_id: int) -> dict:
    """Fetch last 7 days of glucose readings for the user."""
    history = get_cgm_history(user_id, limit=21)
    latest  = get_latest_cgm(user_id)
    readings = [
        f"{h['logged_at'][:16].replace('T',' ')} — {h['reading']} mg/dL ({_classify(h['reading'])})"
        for h in reversed(history)
    ]
    return {"latest": latest, "count": len(history), "readings": readings}


def make_cgm_agent() -> Agent:
    return Agent(
        name="CGMAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[log_glucose_reading, fetch_glucose_history],
        instructions=[
            "You have two tools: log_glucose_reading and fetch_glucose_history.",
            "Rule 1: If the message contains a glucose NUMBER → call log_glucose_reading.",
            "Rule 2: If asking for history, past readings, trends → call fetch_glucose_history.",
            "Rule 3: If unclear, ask whether they want to log or see history.",
            "Valid range per spec is 80–300 mg/dL. Flag if outside this range.",
            "For log: ONE sentence — state reading and status. If alert, mention it.",
            "For history: list each reading on its own line from the 'readings' field.",
            "No markdown, no headers, no bullet points.",
        ],
        markdown=False,
    )
