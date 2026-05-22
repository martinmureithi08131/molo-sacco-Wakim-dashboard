import json
import os
import uuid

DB_FILE = "database.json"


def load_db():

    if not os.path.exists(DB_FILE):
        return {}

    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_db(db):

    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def add_record(collection, record):

    db = load_db()

    if collection not in db:
        db[collection] = []

    record["_id"] = str(uuid.uuid4())

    db[collection].append(record)

    save_db(db)


def get_records(collection):

    db = load_db()

    return db.get(collection, [])


def delete_record(collection, record_id):

    db = load_db()

    if collection not in db:
        return False

    original_len = len(db[collection])

    db[collection] = [
        r for r in db[collection]
        if r.get("_id") != record_id
    ]

    save_db(db)

    return len(db[collection]) < original_len


def update_record(collection, record_id, updated_record):

    db = load_db()

    if collection not in db:
        return False

    for i, record in enumerate(db[collection]):

        if record.get("_id") == record_id:

            updated_record["_id"] = record_id

            db[collection][i] = updated_record

            save_db(db)

            return True

    return False
