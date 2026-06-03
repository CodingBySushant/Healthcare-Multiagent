"""
Interrupt Agent — answers general health queries using user profile from DB,
then gracefully routes the user back to their previous flow.
"""
import os
from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools import tool
from agents.db import get_user

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

FLOW_LABELS = {
    "cgm":       "glucose logging",
    "mood":      "mood tracking",
    "food":      "food intake logging",
    "meal_plan": "meal plan",
    "main":      "the main menu",
}


@tool
def answer_query(user_id: int, query: str, previous_flow: str = "main") -> dict:
    """
    Answer a general health query personalised to the user's conditions.
    Returns answer and a routing message back to the previous flow.
    """
    from groq import Groq as GroqClient

    user = get_user(user_id)
    profile_note = ""
    if user:
        conditions = [c for c in user.get("conditions", []) if c != "None"]
        dietary    = user.get("dietary_pref", "")
        limits     = user.get("limitations", "")
        if conditions: profile_note += f"Medical conditions: {', '.join(conditions)}. "
        if dietary:    profile_note += f"Dietary preference: {dietary}. "
        if limits and limits != "None": profile_note += f"Limitations: {limits}. "

    system = (
        "You are a knowledgeable healthcare assistant. "
        f"User profile — {profile_note}"
        "Give specific, personalised advice using the profile. "
        "Never ask the user to re-state their condition. "
        "3–4 sentences max. Plain text only, no markdown."
    )

    client = GroqClient(api_key=GROQ_API_KEY)
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": query},
            ],
            max_tokens=200, temperature=0.3,
        )
        answer = resp.choices[0].message.content.strip()
    except Exception:
        answer = "I'm having trouble connecting. Please try again."

    flow_label = FLOW_LABELS.get(previous_flow, "where we left off")
    resume = f"\n\nGetting you back to {flow_label} — feel free to continue!" if previous_flow != "main" else ""

    return {"answer": answer + resume}


def make_interrupt_agent() -> Agent:
    return Agent(
        name="InterruptAgent",
        model=Groq(id="llama-3.3-70b-versatile", api_key=GROQ_API_KEY),
        tools=[answer_query],
        instructions=[
            "Call answer_query with user_id, the question, and the previous_flow.",
            "Extract previous_flow from the message context (e.g. 'Previous flow: cgm').",
            "Output ONLY the answer string from the result. No steps, no headers.",
        ],
        markdown=False,
    )
