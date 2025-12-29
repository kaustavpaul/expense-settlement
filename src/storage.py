import uuid
from .storage_drive import get_drive_service, save_to_drive, load_from_drive, is_drive_connected
from .storage_github import get_github_repo, save_to_github, load_from_github, is_github_connected, save_to_local, load_from_local
from .storage_sheets import sync_to_sheet, is_sheets_connected

def create_session(data):
    """Creates a new session and saves it to all available providers."""
    session_id = str(uuid.uuid4())
    
    # 1. Local
    save_to_local(session_id, data)
    
    # 2. Google Drive
    if is_drive_connected():
        service = get_drive_service()
        if service:
            save_to_drive(service, session_id, data)
            
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
    
    # 2. Google Drive
    if is_drive_connected():
        service = get_drive_service()
        if service:
            save_to_drive(service, session_id, data)
            
    # 3. Google Sheets (Backup layer)
    if is_sheets_connected():
        sync_to_sheet(session_id, data)
            
    # 4. GitHub
    if is_github_connected():
        repo = get_github_repo()
        if repo:
            save_to_github(repo, session_id, data)

def load_session(session_id):
    """Loads session data from the first available provider (Local > Drive > GitHub)."""
    # 1. Try Local
    data = load_from_local(session_id)
    if data:
        return data
        
    # 2. Try Google Drive
    if is_drive_connected():
        service = get_drive_service()
        if service:
            data = load_from_drive(service, session_id)
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
    if is_drive_connected():
        providers.append("Google Drive")
    if is_sheets_connected():
        providers.append("Google Sheets")
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
