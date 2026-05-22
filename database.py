from pymongo import MongoClient
from bson import ObjectId

# MongoDB Connection
MONGO_URI = "YOUR_MONGODB_CONNECTION_STRING"

client = MongoClient(MONGO_URI)

db = client["molo_sacco_db"]


# ─────────────────────────────────────────────
# ADD RECORD
# ─────────────────────────────────────────────
def add_record(table, data):

    collection = db[table]

    collection.insert_one(data)


# ─────────────────────────────────────────────
# GET RECORDS
# ─────────────────────────────────────────────
def get_records(table):

    collection = db[table]

    return list(collection.find())


# ─────────────────────────────────────────────
# UPDATE RECORD
# ─────────────────────────────────────────────
def update_record(table, record_id, updated_data):

    collection = db[table]

    result = collection.update_one(
        {"_id": ObjectId(record_id)},
        {"$set": updated_data}
    )

    return result.modified_count > 0


# ─────────────────────────────────────────────
# DELETE RECORD
# ─────────────────────────────────────────────
def delete_record(table, record_id):

    collection = db[table]

    result = collection.delete_one(
        {"_id": ObjectId(record_id)}
    )

    return result.deleted_count > 0
