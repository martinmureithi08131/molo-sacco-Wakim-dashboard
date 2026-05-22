import json
import os
import uuid

DB_FILE = "database.json"

# =========================================
# LOAD DATABASE
# =========================================

def get_db():

    if not os.path.exists(DB_FILE):

        with open(DB_FILE, "w") as f:
            json.dump(
                {
                    "daily_earnings": []
                },
                f,
                indent=2
            )

    try:

        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:

        return {
            "daily_earnings": []
        }

# =========================================
# SAVE DATABASE
# =========================================

def save_db(db):

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# =========================================
# ADD RECORD
# =========================================

def add_record(collection, record):

    db = get_db()

    if collection not in db:
        db[collection] = []

    # Prevent duplicates
    for existing in db[collection]:

        if (
            existing.get("date")
            == record.get("date")
            and
            existing.get("gross_earnings")
            == record.get("gross_earnings")
            and
            existing.get("entered_by")
            == record.get("entered_by")
        ):

            return {
                "success": False,
                "message": "Duplicate transaction detected."
            }

    record["_id"] = str(uuid.uuid4())

    db[collection].append(record)

    save_db(db)

    return {
        "success": True,
        "message": "Transaction saved successfully."
    }

# =========================================
# GET RECORDS
# =========================================

def get_records(collection):

    db = get_db()

    return db.get(collection, [])

# =========================================
# UPDATE RECORD
# =========================================

def update_record(collection, record_id, updated_record):

    db = get_db()

    if collection not in db:
        return False

    for i, record in enumerate(db[collection]):

        if record["_id"] == record_id:

            updated_record["_id"] = record_id

            db[collection][i] = updated_record

            save_db(db)

            return True

    return False

# =========================================
# DELETE RECORD
# =========================================

def delete_record(collection, record_id):

    db = get_db()

    if collection not in db:
        return False

    original_length = len(db[collection])

    db[collection] = [

        r for r in db[collection]

        if r["_id"] != record_id
    ]

    save_db(db)

    return len(db[collection]) < original_length
