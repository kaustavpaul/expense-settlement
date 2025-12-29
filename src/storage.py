import uuid
from .storage_github import get_github_repo, save_to_github, load_from_github, is_github_connected, save_to_local, load_from_local
from .storage_sheets import save_session_to_sheet, load_session_from_sheet, list_sessions_from_sheet, is_sheets_connected

def create_session(data):
    """Creates a new session and saves it to Cloud (Sheets) and GitHub."""
    session_id = str(uuid.uuid4())
    
    # 1. Local
    save_to_local(session_id, data)
    
    # 2. Google Sheets (Primary DB)
    if is_sheets_connected():
        save_session_to_sheet(session_id, data)
            
    # 3. GitHub
    if is_github_connected():
        repo = get_github_repo()
        if repo:
            save_to_github(repo, session_id, data)
            
    return session_id

def update_session(session_id, data):
    """Updates an existing session across all available providers."""
    # 1. Local
    save_to_local(session_id, data)
    
    # 2. Google Sheets (Primary DB)
    if is_sheets_connected():
        return save_session_to_sheet(session_id, data)
            
    # 3. GitHub
    if is_github_connected():
        repo = get_github_repo()
        if repo:
            save_to_github(repo, session_id, data)

def load_session(session_id):
    """Loads session data from the first available provider (Local > Sheets > GitHub)."""
    # 1. Try Local
    data = load_from_local(session_id)
    if data:
        return data
        
    # 2. Try Google Sheets
    if is_sheets_connected():
        data = load_session_from_sheet(session_id)
        if data:
            save_to_local(session_id, data) # Sync local
            return data
                
    # 3. Try GitHub
    if is_github_connected():
        repo = get_github_repo()
        if repo:
            data = load_from_github(repo, session_id)
            if data:
                save_to_local(session_id, data) # Sync local
                return data
                
    return None

def get_storage_status():
    """Returns a string describing the current storage configuration."""
    providers = []
    if is_sheets_connected():
        providers.append("Google Sheets (DB)")
    if is_github_connected():
        providers.append("GitHub")
    
    if not providers:
        return "Local Storage Only"
    
    # Check for credentials file
    cred_file = "kaustavsampleproject-2dda07854172.json"
    import os
    info = ""
    if os.path.exists(cred_file):
        info = " (Local Cert Found)"
        
    return f"Active Cloud: {', '.join(providers)}{info}"

def get_available_sessions():
    """Returns a list of available sessions from Cloud Storage."""
    sessions = []
    if is_sheets_connected():
        sessions = list_sessions_from_sheet()
    return sessions
