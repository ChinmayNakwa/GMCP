import json
from datetime import datetime, timedelta, UTC
from fastmcp import FastMCP
from google_auth.services.google_calendar import get_calendar_service

mcp = FastMCP("GoogleCalendar")

def create_error_response(message: str, details: str = None) -> str:
    error_obj = {"error": message}
    if details:
        error_obj["details"] = details
    return json.dumps(error_obj)

@mcp.tool()
def list_events(user_id: str, calendar_id: str = 'primary', max_results: int = 10, time_min: str = None) -> str:
    """
    Lists events from a specified calendar. Defaults to the primary calendar.
    If time_min is not provided, it lists upcoming events.
    time_min should be in ISO 8601 format (e.g., '2024-05-21T00:00:00Z').
    Returns a JSON string of the event list.
    """
    service = get_calendar_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Calendar.")
    
    try:
        if not time_min:
            time_min = datetime.now(UTC).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id, timeMin=time_min, maxResults=max_results,
            singleEvents=True, orderBy='startTime'
        ).execute()

        return json.dumps(events_result.get('items', []))
    except Exception as e:
        return create_error_response("An API error occurred during list_events.", str(e))
    
@mcp.tool()
def create_event(user_id: str, summary: str, start_datetime: str, end_datetime: str, calendar_id: str = 'primary', attendees: list = None, recurrence: str = None, color_id: str = None) -> str:
    """
    Creates a new event on a specified calendar. Defaults to the primary calendar.
    'start_datetime' and 'end_datetime' must be in ISO 8601 format (e.g., '2024-05-21T10:00:00-07:00').
    Returns the created event object as a JSON string.
    """
    service = get_calendar_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Calendar.")

    event_body = {
        'summary': summary,
        'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
        'end': {'dateTime': end_datetime, 'timeZone': 'UTC'},
    }
    if attendees:
        new_attendees = []
        for attendee in attendees:
            if isinstance(attendee, dict) and 'email' in attendee:
                new_attendees.append(attendee)
            elif isinstance(attendee, str):
                new_attendees.append({'email': attendee})
        if new_attendees:
            event_body['attendees'] = new_attendees

    if recurrence:
        event_body['recurrence'] = [recurrence]

    if color_id:
        event_body['colorId'] = color_id

    try:
        created_event = service.events().insert(
                                            calendarId=calendar_id, 
                                            body=event_body,
                                            sendNotifications=True,
                                        ).execute()
        return json.dumps(created_event)
    except Exception as e:
        return create_error_response("An API error occurred during create_event.", str(e))
    
@mcp.tool()
def delete_event(user_id: str, event_id: str, calendar_id: str = 'primary') -> str:
    """Deletes an event from a specified calendar using its unique event_id."""
    service = get_calendar_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Calendar.")
    
    try:    
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return json.dumps({"status": "success", "message": f"Event {event_id} deleted."})
    except Exception as e:
        return create_error_response(f"Could not delete event {event_id}.", str(e))

@mcp.tool()
def update_event(user_id: str, event_id: str, calendar_id: str = 'primary', updated_summary: str = None, start_datetime: str = None, end_datetime: str = None, attendees: list = None, recurrence: str = None, color_id: str = None) -> str:
    """
    Updates an existing event. Fetches the event first and only modifies the provided fields.
    All other fields like attendees and location will be preserved.
    """
    service = get_calendar_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Calendar.")
    
    try:
        # Get the existing event
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

        # Update only the provided fields
        if updated_summary:
            event['summary'] = updated_summary
        if start_datetime:
            event['start']['dateTime'] = start_datetime
        if end_datetime:
            event['end']['dateTime'] = end_datetime
        if attendees is not None:
            new_attendees = []
            for attendee in attendees:
                if isinstance(attendee, dict) and 'email' in attendee:
                    new_attendees.append(attendee)
                elif isinstance(attendee, str):
                    new_attendees.append({'email': attendee})
            event['attendees'] = new_attendees
        if recurrence:
            event['recurrence'] = [recurrence]
        if color_id:
            event['colorId'] = color_id
        # Update the event
        updated_event = service.events().update(
            calendarId=calendar_id,
            eventId=event_id,
            body=event,
            sendNotifications=True,
        ).execute()
        
        return json.dumps(updated_event)
    except Exception as e:
        return create_error_response(f"Could not update event: {e}")
    
@mcp.tool()
def get_event_by_id(user_id: str, event_id: str, calendar_id: str = 'primary') -> str:
    """Retrieves a specific event by its ID."""
    service = get_calendar_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Calendar.")
    
    try:
        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        return json.dumps(event)
    except Exception as e:
        return create_error_response(f"Failed to retrieve event: {e}")

if __name__ == "__main__":
    print("--- Google Calendar MCP Server starting up... ---")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001)
