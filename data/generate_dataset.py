"""
Synthetic dataset generator for 100 healthcare users.
Uses Faker for names/cities and Groq LLM for realistic medical condition descriptions.
Run: python generate_dataset.py
"""
import sqlite3, random, json, os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker("en_IN")
random.seed(42)
DB_PATH = os.path.join(os.path.dirname(__file__), "healthcare.db")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

CITIES           = ["Mumbai", "Delhi", "Bangalore", "Pune", "Hyderabad", "Chennai", "Kolkata"]
DIETARY_PREFS    = ["vegetarian", "non-vegetarian", "vegan"]
MEDICAL_CONDITIONS = [
    "Type 2 Diabetes", "Hypertension", "Hypothyroidism",
    "GERD", "High Cholesterol", "Obesity", "Anemia",
    "Lactose Intolerance", "Arthritis", "None",
]
PHYSICAL_LIMITATIONS = [
    "None", "Mobility issues", "Swallowing difficulties",
    "Arthritis", "Low vision", "Chronic back pain",
]
MOODS = ["happy","sad","excited","tired","anxious","calm","irritable","neutral"]


def llm_generate_condition_notes(conditions: list) -> str:
    """Use Groq LLM to generate a realistic one-line health note for the user."""
    if not GROQ_API_KEY or conditions == ["None"]:
        return ""
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        cond_str = ", ".join(conditions)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content":
                f"Write ONE short realistic clinical note (under 20 words) for a patient with: {cond_str}. Plain text only."}],
            max_tokens=40, temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return ""


def get_cgm_range(conditions: list) -> tuple:
    if "Type 2 Diabetes" in conditions: return (110, 290)
    if "Obesity" in conditions or "High Cholesterol" in conditions: return (90, 160)
    return (80, 120)


def create_schema(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT,
            city TEXT, dietary_pref TEXT, conditions TEXT,
            limitations TEXT, cgm_min INTEGER, cgm_max INTEGER,
            health_note TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS mood_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            mood TEXT, mood_score INTEGER, logged_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS cgm_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            reading INTEGER, flagged INTEGER DEFAULT 0, logged_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
            description TEXT, carbs_g REAL, protein_g REAL,
            fat_g REAL, logged_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS session_state (
            user_id INTEGER PRIMARY KEY, active_flow TEXT DEFAULT 'main',
            last_active_at TEXT, FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()


def generate_users(conn):
    diet_pool = DIETARY_PREFS * 33 + ["vegetarian"]
    random.shuffle(diet_pool)
    users = []
    for i in range(1, 101):
        conditions = random.sample(MEDICAL_CONDITIONS, k=random.randint(1, 3))
        if len(conditions) > 1 and "None" in conditions:
            conditions.remove("None")
        limitation = random.choice(PHYSICAL_LIMITATIONS)
        cgm_min, cgm_max = get_cgm_range(conditions)
        # LLM generates a realistic health note
        health_note = llm_generate_condition_notes(conditions)
        users.append((
            i, fake.first_name(), fake.last_name(), random.choice(CITIES),
            diet_pool[i-1], json.dumps(conditions), limitation,
            cgm_min, cgm_max, health_note
        ))
    conn.executemany(
        "INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?)", users
    )
    conn.commit()
    print(f"✓ Inserted {len(users)} users")


def generate_historical_logs(conn):
    mood_score_map = {
        "happy":8,"excited":9,"calm":7,"neutral":5,
        "tired":3,"sad":2,"anxious":4,"irritable":3,
    }
    sample_meals = [
        "Oatmeal with banana","Dal chawal with sabzi","Grilled paneer tikka",
        "Idli sambar","Chicken curry with rice","Mixed vegetable soup",
        "Rajma with jeera rice","Egg bhurji with toast","Fruit salad with yogurt",
        "Whole wheat roti with dal",
    ]
    users = conn.execute("SELECT id, cgm_min, cgm_max FROM users").fetchall()
    now = datetime.now()
    mood_rows, cgm_rows, food_rows = [], [], []
    for user_id, cgm_min, cgm_max in users:
        for day_offset in range(7, 0, -1):
            base_dt = now - timedelta(days=day_offset)
            for hour in [8, 13, 19]:
                reading = random.randint(cgm_min, cgm_max)
                flagged = 1 if reading < 80 or reading > 300 else 0
                cgm_rows.append((user_id, reading, flagged,
                    base_dt.replace(hour=hour, minute=random.randint(0,59)).isoformat()))
            mood = random.choice(MOODS)
            mood_rows.append((user_id, mood, mood_score_map[mood],
                base_dt.replace(hour=9).isoformat()))
            for meal in random.sample(sample_meals, 2):
                food_rows.append((user_id, meal,
                    round(random.uniform(20,80),1), round(random.uniform(5,40),1),
                    round(random.uniform(3,25),1),
                    base_dt.replace(hour=random.choice([8,13,19])).isoformat()))
    conn.executemany("INSERT INTO cgm_log (user_id,reading,flagged,logged_at) VALUES (?,?,?,?)", cgm_rows)
    conn.executemany("INSERT INTO mood_log (user_id,mood,mood_score,logged_at) VALUES (?,?,?,?)", mood_rows)
    conn.executemany("INSERT INTO food_log (user_id,description,carbs_g,protein_g,fat_g,logged_at) VALUES (?,?,?,?,?,?)", food_rows)
    conn.commit()
    print(f"✓ Seeded {len(cgm_rows)} CGM, {len(mood_rows)} mood, {len(food_rows)} food logs")


def validate_dataset(conn):
    total    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    diabetic = conn.execute("SELECT COUNT(*) FROM users WHERE conditions LIKE '%Type 2 Diabetes%'").fetchone()[0]
    cities   = conn.execute("SELECT COUNT(DISTINCT city) FROM users").fetchone()[0]
    diets    = conn.execute("SELECT dietary_pref, COUNT(*) FROM users GROUP BY dietary_pref").fetchall()
    with_notes = conn.execute("SELECT COUNT(*) FROM users WHERE health_note != ''").fetchone()[0]
    print(f"\n── Dataset validation ──")
    print(f"  Total users       : {total}")
    print(f"  Diabetic          : {diabetic}")
    print(f"  Cities            : {cities}")
    print(f"  LLM health notes  : {with_notes}")
    for diet, cnt in diets:
        print(f"  {diet:20s}: {cnt}")
    print("── OK ──\n")


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)
    print("Generating users (LLM health notes via Groq)...")
    generate_users(conn)
    generate_historical_logs(conn)
    validate_dataset(conn)
    conn.close()
    print(f"Database written to {DB_PATH}")
