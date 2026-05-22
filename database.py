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

    # Create empty database if missing
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

    # Generate unique transaction ID
    record["_id"] = str(uuid.uuid4())

    # Save record
    db[collection].append(record)

    save_db(db)

    return record["_id"]

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

            # Update record
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

    # Check if deletion happened
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
