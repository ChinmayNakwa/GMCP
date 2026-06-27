from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from models.db import load_token, save_token
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service(user_id: str):
    token_data = load_token(user_id, 'gmail')
    if not token_data:
        return None
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(user_id, 'gmail', json.loads(creds.to_json()))
    try:
        return build('gmail', 'v1', credentials=creds)
    except Exception as e:
        print(f"Error building gmail service: {e}")
        return None