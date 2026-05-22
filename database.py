import json
import os
from datetime import datetime

DB_FILE = "data.json"

SCHEMA = {
    "daily_earnings": [],
    "expenses": [],
    "maintenance": [],
    "insurance": [],
    "debts": [],
    "projected": [],
    "future_expenses": [],
    "monthly_earnings": [],
}

def load_db() -> dict:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            db = json.load(f)
        for key in SCHEMA:
            if key not in db:
                db[key] = []
        return db
    return dict(SCHEMA)

def save_db(db: dict):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, default=str)

def add_record(table: str, record: dict):
    db = load_db()
    record["_id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    db[table].append(record)
    save_db(db)

def get_records(table: str) -> list:
    return load_db().get(table, [])