import os
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from agents.db import get_user, user_exists, set_session_flow

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


@tool
def greet_by_id(user_id: int) -> dict:
    """Validate user ID and return greeting data."""
    if not user_exists(user_id):
        return {
            "valid": False,
            "greeting": f"User ID {user_id} not found. Please enter a valid ID between 1 and 100.",
        }
    user = get_user(user_id)
    set_session_flow(user_id, "main")
    conditions = [c for c in user["conditions"] if c != "None"]
    cond_note = f" I can see you have {', '.join(conditions)} on record." if conditions else ""
    greeting = (
        f"Hello, {user['first_name']}! 👋 Welcome to HealthPulse. "
        f"You're based in {user['city']}.{cond_note} "
        f"I can help you track mood, glucose, and meals. What would you like to do first?"
    )
    return {"valid": True, "greeting": greeting, "user": {
        "id": user["id"], "first_name": user["first_name"],
        "last_name": user["last_name"], "city": user["city"],
        "dietary_pref": user["dietary_pref"], "conditions": user["conditions"],
        "limitations": user["limitations"],
    }}


def make_greeting_agent() -> Agent:
    return Agent(
        name="GreetingAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[greet_by_id],
        instructions=[
            "Extract the user ID number from the message and call greet_by_id.",
            "Output ONLY the greeting string. Nothing else — no steps, no headers, no analysis.",
        ],
        markdown=False,
    )
