import firebase_admin
from firebase_admin import credentials, firestore
import os

_db = None


def get_db():
    global _db

    if _db is None:

        if not firebase_admin._apps:

            key_path = os.path.join(
                os.path.dirname(__file__),
                "firebase_key.json"
            )

            cred = credentials.Certificate(key_path)

            firebase_admin.initialize_app(cred)

        _db = firestore.client()

    return _db


# ─────────────────────────────────────────────
# ADD RECORD
# ─────────────────────────────────────────────
def add_record(table: str, record: dict):

    db = get_db()

    db.collection(table).add(record)


# ─────────────────────────────────────────────
# GET RECORDS
# ─────────────────────────────────────────────
def get_records(table: str) -> list:

    db = get_db()

    docs = db.collection(table).stream()

    records = []

    for doc in docs:

        data = doc.to_dict()

        data["_id"] = doc.id

        records.append(data)

    return records


# ─────────────────────────────────────────────
# UPDATE RECORD
# ─────────────────────────────────────────────
def update_record(table: str, record_id: str, updated_data: dict):

    db = get_db()

    try:
        db.collection(table).document(record_id).update(updated_data)

        return True

    except Exception:
        return False


# ─────────────────────────────────────────────
# DELETE RECORD
# ─────────────────────────────────────────────
def delete_record(table: str, record_id: str):

    db = get_db()

    try:
        db.collection(table).document(record_id).delete()

        return True

    except Exception:
        return False
