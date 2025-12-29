import json
import os
import streamlit as st
from github import Github, GithubException

SESSIONS_DIR = "sessions"
# Safely load secrets
try:
    GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN")
    REPO_NAME = st.secrets.get("REPO_NAME")
except FileNotFoundError:
    GITHUB_TOKEN = None
    REPO_NAME = None

@st.cache_resource
def get_github_repo():
    """Authenticates with GitHub and caches the repository object."""
    if not GITHUB_TOKEN or not REPO_NAME:
        return None
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        return repo
    except Exception as e:
        print(f"GitHub Error: {e}")
        return None

def save_to_local(session_id, data):
    """Saves session data to a local JSON file."""
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)
    
    file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)
    return file_path

def load_from_local(session_id):
    """Loads session data from local JSON file."""
    local_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return json.load(f)
    return None

def save_to_github(repo, session_id, data):
    """Pushes session data to the GitHub repository."""
    file_path = f"{SESSIONS_DIR}/{session_id}.json"
    json_content = json.dumps(data, indent=4)
    
    try:
        try:
            # Update existing file
            contents = repo.get_contents(file_path)
            repo.update_file(file_path, f"Update session {session_id}", json_content, contents.sha)
            return True
        except GithubException:
            # Create new file
            repo.create_file(file_path, f"Create session {session_id}", json_content)
            return True
    except Exception as e:
        print(f"Failed to save to GitHub: {e}")
        return False

def load_from_github(repo, session_id):
    """Loads session data from GitHub."""
    try:
        file_path = f"{SESSIONS_DIR}/{session_id}.json"
        contents = repo.get_contents(file_path)
        data = json.loads(contents.decoded_content.decode("utf-8"))
        # Sync to local
        save_to_local(session_id, data)
        return data
    except Exception as e:
        print(f"Failed to load from GitHub: {e}")
        return None

def is_github_connected():
    """Returns True if GitHub credentials seem to be present."""
    return bool(GITHUB_TOKEN and REPO_NAME)
