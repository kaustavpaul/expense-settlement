import streamlit as st
import gspread
import json
import pandas as pd
from datetime import datetime
from .utils import load_google_credentials

# Constants
SHEET_NAME = "Expense Settlement DB" # User must create this sheet
WORKSHEET_NAME = "Sessions"

@st.cache_resource
def get_sheets_client():
    """Authenticates with Google Sheets and caches the client."""
    creds_info = load_google_credentials()
    if not creds_info:
        return None
    
    try:
        from google.oauth2 import service_account
        # Handle stringified JSON if needed
        if isinstance(creds_info, str):
            creds_info = json.loads(creds_info)
            
        creds = service_account.Credentials.from_service_account_info(
            creds_info, 
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Google Sheets Authentication Error: {e}")
        return None

def is_sheets_connected():
    """Checks if Sheets credentials are available."""
    return load_google_credentials() is not None

def _get_or_create_worksheet(client):
    """Helper to get the database worksheet."""
    try:
        # Open the main spreadsheet
        # We try to open by name. If user hasn't created it, this will fail.
        sheet = client.open(SHEET_NAME)
        
        try:
            ws = sheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            # Create the worksheet if it doesn't exist (allowed if bot is editor)
            ws = sheet.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=10)
            # Initialize Headers
            ws.append_row(["Session ID", "Last Modified", "Description", "JSON Data"])
            
        return ws, sheet.url
    except Exception as e:
        print(f"Error accessing sheetDB: {e}")
        return None, None

def save_session_to_sheet(session_id, data):
    """Upserts session data into the Google Sheet."""
    client = get_sheets_client()
    if not client:
        return False

    ws, sheet_url = _get_or_create_worksheet(client)
    if not ws:
        # Fallback: Try creating the spreadsheet document if it doesn't exist?
        # No, we can't create files (quota). User MUST create 'Expense Settlement DB'.
        st.error(f"Could not find Google Sheet named '{SHEET_NAME}'. Please create it and share with the bot.")
        return False

    # Prepare data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    desc = f"Payer: {data.get('payer_names_input', '')[:20]}..."
    json_payload = json.dumps(data)
    
    try:
        # Check if ID exists
        cell = ws.find(session_id)
        if cell:
            # Update existing row
            # Row mapping: ID(1), Modified(2), Desc(3), JSON(4)
            ws.update_cell(cell.row, 2, timestamp)
            ws.update_cell(cell.row, 3, desc)
            ws.update_cell(cell.row, 4, json_payload)
        else:
            # Append new row
            ws.append_row([session_id, timestamp, desc, json_payload])
            
        return sheet_url
    except Exception as e:
        print(f"Error saving to SheetDB: {e}")
        return False

def load_session_from_sheet(session_id):
    """Loads session data from the Google Sheet."""
    client = get_sheets_client()
    if not client:
        return None

    ws, _ = _get_or_create_worksheet(client)
    if not ws:
        return None

    try:
        cell = ws.find(session_id)
        if cell:
            # Fetch JSON data from column 4
            json_str = ws.cell(cell.row, 4).value
            return json.loads(json_str)
    except Exception as e:
        print(f"Error loading from SheetDB: {e}")
    
    return None

def list_sessions_from_sheet():
    """Lists all available sessions [id, display_name]."""
    client = get_sheets_client()
    if not client:
        return []

    ws, _ = _get_or_create_worksheet(client)
    if not ws:
        return []

    try:
        # Get all records
        records = ws.get_all_records()
        # Expecting keys matching headers: "Session ID", "Last Modified", "Description"
        sessions = []
        for r in records:
            if r['Session ID']:
                sessions.append({
                    'id': str(r['Session ID']),
                    'display': f"{r['Last Modified']} - {r['Description']}"
                })
        # Sort by date desc
        sessions.sort(key=lambda x: x['display'], reverse=True)
        return sessions
    except Exception as e:
        print(f"Error listing from SheetDB: {e}")
        return []
