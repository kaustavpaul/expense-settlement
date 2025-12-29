import streamlit as st
import json
import os
import gspread
from .utils import load_google_credentials

# Optional custom title
CREDENTIALS_FILE = "kaustavsampleproject-2dda07854172.json"
SHEET_NAME = "Expense Settlement - Cloud Backups"

@st.cache_resource
def get_sheets_client():
    """Authenticates with Google Sheets and caches the client."""
    creds_info = load_google_credentials()
    if not creds_info:
        return None
    
    try:
        from google.oauth2 import service_account
        if isinstance(creds_info, str):
            creds_info = json.loads(creds_info)
            
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Google Sheets Authentication Error: {e}")
        return None

def sync_to_sheet(session_id, data):
    """Backs up a session summary to the Google Spreadsheet."""
    client = get_sheets_client()
    if not client:
        return False
        
    try:
        # 1. Open or Create the spreadsheet
        try:
            sh = client.open(SHEET_NAME)
        except gspread.exceptions.SpreadsheetNotFound:
            sh = client.create(SHEET_NAME)
            # Add header
            worksheet = sh.get_worksheet(0)
            worksheet.append_row(["Session ID", "Payer", "Participants", "Total Amount", "Last Updated"])
            
            # SHARE IT!
            # Try to share with the user's email if configured
            user_email = None
            try:
                user_email = st.secrets.get("USER_EMAIL")
            except:
                pass
            
            if user_email:
                try:
                    sh.share(user_email, perm_type='user', role='writer')
                    print(f"Shared sheet with {user_email}")
                except Exception as share_err:
                    print(f"Error sharing sheet: {share_err}")

        worksheet = sh.get_worksheet(0)
        
        # 2. Format row data
        payer = data.get('payer_names_input', 'N/A')
        participants = data.get('participant_names_input', 'N/A')
        
        # Calculate approximate total
        total_spent = 0
        if 'expenses_data' in data:
            total_spent = sum(float(row.get('Amount', 0)) for row in data['expenses_data'])
        
        import datetime
        row_data = [
            session_id,
            payer,
            participants,
            total_spent,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        # 3. Check if session exists to update or append
        cell = worksheet.find(session_id)
        if cell:
            worksheet.update(f"A{cell.row}:E{cell.row}", [row_data])
        else:
            worksheet.append_row(row_data)
            
        return sh.url
    except Exception as e:
        print(f"Google Sheets Sync Error: {e}")
        return False

def is_sheets_connected():
    """Checks if Sheets credentials are available."""
    return load_google_credentials() is not None
