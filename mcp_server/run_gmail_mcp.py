import json
import base64
from datetime import datetime, timedelta, UTC
from fastmcp import FastMCP
import os
from typing import Any

import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from google_auth.services.google_mail import get_gmail_service

mcp = FastMCP("Gmail")

def create_error_response(message: str, details: str = None) -> str:
    error_obj = {"error": message}
    if details:
        error_obj["details"] = details
    return json.dumps(error_obj)

@mcp.tool()
def list_emails(user_id: str, query: str = "is:inbox", max_results: int = 5) -> str:
    """
    Lists emails matching a query. Uses standard Gmail search syntax.
    Examples: 'from:boss@company.com is:unread', 'subject:"Project Update"'
    """
    service = get_gmail_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Gmail")
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get("messages", [])
        if not messages:
            return "No emails found matching the query."

        # Just return the list of message IDs
        message_ids = [msg["id"] for msg in messages]
        return json.dumps({"message_ids": message_ids})
    except Exception as e:
        return create_error_response("An API error occured during list_emails.", str(e))

@mcp.tool()
def get_email_details(user_id: str, message_id: str) -> str:
    """Retrieves the full details of a single email using its message_id."""
    service = get_gmail_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Gmail")
    try:
        message = service.users().messages().get(userId='me', id=message_id, format="full").execute()
        return json.dumps(message)
    except Exception as e:
        return create_error_response("An API error occured during get_email_details", str(e))

@mcp.tool()
def send_email(user_id: str, to: str, subject: str, body: str, attachments: list[str] = None) -> str:
    """
    Sends a new email. Can optionally include a list of file paths as attachments.
    'attachments' should be a list of strings, where each string is a valid path to a file.
    """
    service = get_gmail_service(user_id)
    if not service:
        return json.dumps({"error": "Failed to authenticate with Gmail."})
        
    try:
        # 1. Create the root message container
        message = MIMEMultipart()

        #Getting the user's email
        profile = service.users().getProfile(userId="me").execute()
        sender_email = profile['emailAddress']

        # 2. Add the headers
        profile = service.users().getProfile(userId='me').execute()
        message['From'] = sender_email
        message['To'] = to
        message['Subject'] = subject

        # 3. Attach the body of the email as the first part
        message.attach(MIMEText(body, 'plain'))

        # 4. Handle and attach files
        if attachments:
            for file_path in attachments:
                if not os.path.exists(file_path):
                    return json.dumps({"error": f"Attachment file not found: {file_path}"})

                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream' # Default if type is unknown
                
                main_type, sub_type = content_type.split('/', 1)

                # Create the attachment part
                with open(file_path, 'rb') as fp:
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(fp.read())
                
                # Encode the binary attachment data for email transport
                encoders.encode_base64(part)
                
                # Add a header to identify the file
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=os.path.basename(file_path)
                )
                
                # Attach the file part to the root message
                message.attach(part)

        # 5. Prepare the message for the API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        # 6. Send the message
        sent_message = service.users().messages().send(userId="me", body=create_message).execute()
        return json.dumps(sent_message) # Return the full response object for consistency
        
    except Exception as e:
        return json.dumps({"error": f"An API error occurred while sending the email: {e}"})
if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8002)
