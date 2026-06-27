from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from models.db import load_token, save_token
import json

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_sheets_service(user_id: str):
    token_data = load_token(user_id, 'sheets')
    if not token_data:
        return None
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(user_id, 'sheets', json.loads(creds.to_json()))
    try:
        return build('sheets', 'v4', credentials=creds)
    except Exception as e:
        print(f"Error building sheets service: {e}")
        return None