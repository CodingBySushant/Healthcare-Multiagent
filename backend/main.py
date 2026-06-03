#!/usr/bin/env python3
"""
Backend entrypoint.
1. Generates the database if it doesn't exist.
2. Starts the FastAPI server.
"""
import os
import sys

DB_PATH = os.environ.get("DB_PATH", "/app/data/healthcare.db")

if not os.path.exists(DB_PATH):
    print("Database not found — generating synthetic dataset...")
    sys.path.insert(0, "/app")
    from data.generate_dataset import DB_PATH as SCRIPT_DB_PATH
    import sqlite3
    # Override path in the generator module
    import data.generate_dataset as gen
    gen.DB_PATH = DB_PATH
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    gen.create_schema(conn)
    gen.generate_users(conn)
    gen.generate_historical_logs(conn)
    conn.close()
    print("Dataset ready.")

import uvicorn
uvicorn.run(
    "agents.orchestrator:app",
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info",
)
