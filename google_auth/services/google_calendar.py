from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from models.db import load_token, save_token
import json

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service(user_id: str):
    token_data = load_token(user_id, 'calendar')
    if not token_data:
        return None
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(user_id, 'calendar', json.loads(creds.to_json()))
    try:
        return build('calendar', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building calendar service: {e}")
        return None