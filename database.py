import json
import os
import uuid

# =========================================
# DATABASE FILE
# =========================================

DB_FILE = "database.json"

# =========================================
# LOAD DATABASE
# =========================================

def load_db():

    # Create empty database file
    if not os.path.exists(DB_FILE):

        with open(DB_FILE, "w") as f:
            json.dump({}, f)

    try:

        with open(DB_FILE, "r") as f:
            return json.load(f)

    except:

        return {}

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

    db = load_db()

    # Create collection if missing
    if collection not in db:
        db[collection] = []

    # =====================================
    # DUPLICATE CHECK
    # =====================================

    for existing in db[collection]:

        same_date = (
            existing.get("date")
            == record.get("date")
        )

        same_gross = (
            float(existing.get("gross_earnings", 0))
            == float(record.get("gross_earnings", 0))
        )

        same_user = (
            existing.get("entered_by")
            == record.get("entered_by")
        )

        # Prevent duplicate save
        if same_date and same_gross and same_user:

            return {
                "success": False,
                "message": (
                    "Duplicate transaction detected. "
                    "This transaction already exists."
                )
            }

    # =====================================
    # CREATE UNIQUE ID
    # =====================================

    record["_id"] = str(uuid.uuid4())

    # =====================================
    # SAVE RECORD
    # =====================================

    db[collection].append(record)

    save_db(db)

    return {
        "success": True,
        "message": "Transaction saved successfully.",
        "record_id": record["_id"]
    }

# =========================================
# GET ALL RECORDS
# =========================================

def get_records(collection):

    db = load_db()

    return db.get(collection, [])

# =========================================
# GET SINGLE RECORD
# =========================================

def get_record_by_id(collection, record_id):

    db = load_db()

    if collection not in db:
        return None

    for record in db[collection]:

        if record.get("_id") == record_id:
            return record

    return None

# =========================================
# UPDATE RECORD
# =========================================

def update_record(collection, record_id, updated_record):

    db = load_db()

    if collection not in db:
        return False

    for i, record in enumerate(db[collection]):

        if record.get("_id") == record_id:

            # Preserve original ID
            updated_record["_id"] = record_id

            db[collection][i] = updated_record

            save_db(db)

            return True

    return False

# =========================================
# DELETE RECORD
# =========================================

def delete_record(collection, record_id):

    db = load_db()

    if collection not in db:
        return False

    original_length = len(db[collection])

    db[collection] = [

        record for record in db[collection]

        if record.get("_id") != record_id
    ]

    save_db(db)

    return len(db[collection]) < original_length

# =========================================
# CLEAR COLLECTION
# =========================================

def clear_collection(collection):

    db = load_db()

    if collection in db:

        db[collection] = []

        save_db(db)

        return True

    return False

# =========================================
# COUNT RECORDS
# =========================================

def count_records(collection):

    db = load_db()

    return len(db.get(collection, []))
