# In mcp_server/services/google_mail.py

import os.path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

CREDENTIALS_FILE = 'credentials/credentials.json'
# Use a separate token file for Gmail to keep permissions isolated
TOKEN_FILE = 'credentials/token_gmail.json'

def get_gmail_service():
    """
    Handles the entire Google OAuth 2.0 flow and returns an authenticated
    Google Mail API service object.
    """
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading credentials from {TOKEN_FILE}: {e}")
            if os.path.exists(TOKEN_FILE):
                os.remove(TOKEN_FILE)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Gmail credentials expired. Refreshing token...")
            try: 
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing Gmail token: {e}")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                print("Could not refresh token. Please re-authenticate.")
                return None
        else:
            print("No valid Gmail token found. Starting authentication flow...")
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"ERROR: The credentials file was not found at '{CREDENTIALS_FILE}'")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            # flow.redirect_uri = 'http://localhost:8080/'
            creds = flow.run_local_server(port=0, authorization_prompt_message="")
        
        print(f"Authentication successful. Saving Gmail credentials to {TOKEN_FILE}")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the 'gmail' service, version 'v1'
        service = build('gmail', 'v1', credentials=creds)
        print("Google Mail service created successfully.")
        return service
    except Exception as e:
        print(f"An error occurred while building the service: {e}")
        return None
    
