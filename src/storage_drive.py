import streamlit as st
import json
import os
from googleapiclient.http import MediaInMemoryUpload, MediaIoBaseDownload
import io
from .utils import load_google_credentials

# We expect a service account JSON in st.secrets["GOOGLE_SERVICE_ACCOUNT"]
# This should be the stringified JSON or a dict.
# Safely load secrets
# Safely load optional secrets
try:
    DRIVE_FOLDER_ID = st.secrets.get("DRIVE_FOLDER_ID")
except Exception:
    DRIVE_FOLDER_ID = None

# Credentials path (provided by user)
CREDENTIALS_FILE = "kaustavsampleproject-2dda07854172.json"

@st.cache_resource
def get_drive_service():
    """Authenticates with Google Drive and caches the service."""
    creds_info = load_google_credentials()
    if not creds_info:
        return None
    
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        # If it's a string, parse it. If it's a dict, use as is.
        if isinstance(creds_info, str):
            creds_info = json.loads(creds_info)
            
        creds = service_account.Credentials.from_service_account_info(
            creds_info, scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Google Drive Authentication Error: {e}")
        return None

def find_file(service, name):
    """Finds a file by name. Returns file ID or None."""
    # 1. Try finding in the specific folder if configured
    if DRIVE_FOLDER_ID:
        query = f"name = '{name}' and trashed = false and '{DRIVE_FOLDER_ID}' in parents"
        try:
            results = service.files().list(q=query, fields="files(id, name)").execute()
            files = results.get('files', [])
            if files:
                return files[0]['id']
        except Exception as e:
            print(f"Error finding file {name} in folder: {e}")

    # 2. Fallback: Find anywhere (if not found in folder or no folder configured)
    # This helps if the file was created in 'root' locally but we are now looking on Cloud with a folder ID.
    query = f"name = '{name}' and trashed = false"
    try:
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        if files:
            return files[0]['id']
    except Exception as e:
        print(f"Error finding file {name} globally: {e}")
        
    return None

def list_sessions(service):
    """Lists all available session files (JSON), sorted by newest first."""
    try:
        # Search query: JSON files, not trashed
        query = "mimeType = 'application/json' and trashed = false"
        
        # If folder is configured, prefer searching there, but fall back to global if empty?
        # Actually, let's keep it simple: Search globally for files that look like UUIDs or matching our pattern?
        # For now, searching all JSONs might be too broad. Let's filter by ones that have valid session IDs as names.
        # But names are just UUIDs usually.
        
        # Let's search inside the folder if configured, else global.
        if DRIVE_FOLDER_ID:
            query += f" and '{DRIVE_FOLDER_ID}' in parents"
            
        results = service.files().list(
            q=query, 
            pageSize=20, 
            fields="files(id, name, modifiedTime)", 
            orderBy="modifiedTime desc"
        ).execute()
        
        files = results.get('files', [])
        return files
    except Exception as e:
        print(f"Error listing sessions: {e}")
        return []

def save_to_drive(service, session_id, data):
    """Saves session JSON to Google Drive."""
    filename = f"{session_id}.json"
    json_content = json.dumps(data, indent=4)
    file_id = find_file(service, filename)
    
    media = MediaInMemoryUpload(json_content.encode('utf-8'), mimetype='application/json')
    
    try:
        if file_id:
            # Update existing
            service.files().update(fileId=file_id, media_body=media).execute()
        else:
            # Create new
            file_metadata = {'name': filename}
            if DRIVE_FOLDER_ID:
                file_metadata['parents'] = [DRIVE_FOLDER_ID]
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return True
    except Exception as e:
        print(f"Error saving {filename} to Drive: {e}")
        return False

def load_from_drive(service, session_id):
    """Loads session JSON from Google Drive."""
    filename = f"{session_id}.json"
    file_id = find_file(service, filename)
    
    if not file_id:
        return None
        
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        return json.loads(fh.getvalue().decode('utf-8'))
    except Exception as e:
        print(f"Error loading {filename} from Drive: {e}")
        return None

def is_drive_connected():
    """Checks if Drive credentials are available."""
    return load_google_credentials() is not None
