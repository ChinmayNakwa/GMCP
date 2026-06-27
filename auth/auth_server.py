import sys
import os
sys.path.append('/app')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, redirect, request, session
from models.db import save_token
from google.oauth2.credentials import Credentials
import json, uuid, requests as req

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")

REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:5000/auth/callback")
SCOPES = "https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/meetings.space.created https://www.googleapis.com/auth/drive.file"

import json as _json
with open('credentials/credentials.json') as f:
    _creds = _json.load(f)['web']
CLIENT_ID = _creds['client_id']
CLIENT_SECRET = _creds['client_secret']

@app.route("/auth/start")
def start():
    user_id = request.args.get("user_id", str(uuid.uuid4()))
    session["user_id"] = user_id
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return redirect(auth_url)

@app.route("/auth/callback")
def callback():
    code = request.args.get("code")
    token_response = req.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }).json()

    creds = Credentials(
        token=token_response["access_token"],
        refresh_token=token_response.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES.split()
    )

    user_id = session["user_id"]
    for service in ['calendar', 'gmail', 'meet', 'sheets']:
        save_token(user_id, service, json.loads(creds.to_json()))

    return f"✅ Authenticated! Your user_id: <b>{user_id}</b>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
