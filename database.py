import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import json
from datetime import datetime

SHEET_ID = "1LSB0XGF_0eS9w3DCom71aBymN5YwslMyyn6PDLKwgpo"

def get_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    return gspread.authorize(creds)

def get_sheet(table: str):
    client = get_client()
    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(table)
    except gspread.exceptions.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=table, rows=1000, cols=20)
    return worksheet

def add_record(table: str, record: dict):
    ws = get_sheet(table)
    record["_id"] = datetime.now().strftime("%Y%m%d%H%M%S%f")
    row = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in record.items()}
    existing = ws.get_all_records()
    if not existing:
        ws.append_row(list(row.keys()))
    ws.append_row(list(row.values()))

def get_records(table: str) -> list:
    ws = get_sheet(table)
    records = ws.get_all_records()
    result = []
    for rec in records:
        parsed = {}
        for k, v in rec.items():
            if isinstance(v, str):
                try:
                    parsed[k] = json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    parsed[k] = v
            else:
                parsed[k] = v
        result.append(parsed)
    return result

def update_record(table: str, record_id: str, updated: dict):
    ws = get_sheet(table)
    records = ws.get_all_records()
    for i, rec in enumerate(records):
        if str(rec.get("_id")) == str(record_id):
            updated["_id"] = record_id
            row = {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in updated.items()}
            headers = ws.row_values(1)
            new_row = [row.get(h, "") for h in headers]
            ws.update(f"A{i+2}", [new_row])
            break

def delete_record(table: str, record_id: str):
    ws = get_sheet(table)
    records = ws.get_all_records()
    for i, rec in enumerate(records):
        if str(rec.get("_id")) == str(record_id):
            ws.delete_rows(i + 2)
            break
