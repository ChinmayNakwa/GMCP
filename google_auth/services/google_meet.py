from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google.apps import meet_v2
from models.db import load_token, save_token
import json

SCOPES = ['https://www.googleapis.com/auth/meetings.space.created']

def get_meet_service(user_id: str):
    token_data = load_token(user_id, 'meet')
    if not token_data:
        return None
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_token(user_id, 'meet', json.loads(creds.to_json()))
    try:
        return meet_v2.SpacesServiceClient(credentials=creds)
    except Exception as e:
        print(f"Error building meet service: {e}")
        return None