import pandas as pd
from io import BytesIO
import streamlit as st
import os
import json

def load_google_credentials():
    """Loads Google Service Account credentials from secrets or local JSON file."""
    creds_info = None
    try:
        # Streamlit's st.secrets is preferred
        creds_info = st.secrets.get("GOOGLE_SERVICE_ACCOUNT")
    except Exception:
        pass # Handle below via local file
    
    # Check for local file if secret is missing (provided by user)
    cred_file = "kaustavsampleproject-2dda07854172.json"
    if not creds_info and os.path.exists(cred_file):
        try:
            with open(cred_file, "r") as f:
                creds_info = json.load(f)
        except Exception as e:
            print(f"Error reading local credentials file: {e}")

    # If it's a string (from secrets), parse it.
    if creds_info and isinstance(creds_info, str):
        try:
            creds_info = json.loads(creds_info)
        except Exception:
            pass # Use as is if not valid JSON string
            
    return creds_info

def parse_names(name_string):
    """Parses a comma-separated string of names into a cleaned, sorted, unique list."""
    if not isinstance(name_string, str) or not name_string.strip():
        return []
    # Split, strip whitespace, filter out empty strings, get unique names, and sort
    return sorted(list(set([name.strip() for name in name_string.split(',') if name.strip()])))

def create_empty_dataframe(num_participants=5):
    """Creates an empty DataFrame with the basic structure."""
    columns = ["Expense Type", "Payer", "Amount", "Participants"]
    return pd.DataFrame(columns=columns)

def to_excel(df):
    """Converts a DataFrame to an Excel file in memory, with error handling."""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=True, sheet_name='Report')
        return output.getvalue()
    except Exception as e:
        st.error(f"Failed to create Excel file: {e}")
        return None
