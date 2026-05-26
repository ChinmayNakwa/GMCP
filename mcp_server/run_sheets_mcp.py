import json
from fastmcp import FastMCP
from google_auth.services.google_sheets import get_sheets_service
from googleapiclient.errors import HttpError

mcp = FastMCP("GoogleSheets")

def create_error_response(message: str, details: str = None) -> str:
    error_obj = {"error": message}
    if details:
        error_obj["details"] = details
    return json.dumps(error_obj)


@mcp.tool()
def create_spreadsheet(user_id: str, title: str) -> str:
    """Creates a new Google Spreadsheet and returns its spreadsheetId."""
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        spreadsheet = {"properties": {"title": title}}
        result = service.spreadsheets().create(body=spreadsheet, fields="spreadsheetId").execute()
        spreadsheet_id = result.get("spreadsheetId")
        return json.dumps({"spreadsheetId": spreadsheet_id})
    except HttpError as e:
        return create_error_response("API error during create_spreadsheet.", str(e))


@mcp.tool()
def read_spreadsheet(user_id: str, spreadsheet_id: str, range: str) -> str:
    """
    Reads values from a spreadsheet.
    'range' uses A1 notation e.g. 'Sheet1!A1:D10' or just 'Sheet1'.
    Returns a 2D list of cell values.
    """
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range
        ).execute()
        values = result.get("values", [])
        return json.dumps({"range": result.get("range"), "values": values})
    except HttpError as e:
        return create_error_response("API error during read_spreadsheet.", str(e))


@mcp.tool()
def write_spreadsheet(user_id: str, spreadsheet_id: str, range: str, values: list) -> str:
    """
    Writes values to a spreadsheet.
    'range' uses A1 notation e.g. 'Sheet1!A1'.
    'values' is a 2D list e.g. [['Name', 'Age'], ['Alice', 30]].
    """
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        body = {"values": values}
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return json.dumps({
            "updatedRange": result.get("updatedRange"),
            "updatedRows": result.get("updatedRows"),
            "updatedColumns": result.get("updatedColumns"),
            "updatedCells": result.get("updatedCells"),
        })
    except HttpError as e:
        return create_error_response("API error during write_spreadsheet.", str(e))


@mcp.tool()
def append_rows(user_id: str, spreadsheet_id: str, range: str, values: list) -> str:
    """
    Appends rows after the last row with data in the given range.
    'values' is a 2D list e.g. [['Bob', 25], ['Carol', 28]].
    """
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        body = {"values": values}
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        return json.dumps(result.get("updates", {}))
    except HttpError as e:
        return create_error_response("API error during append_rows.", str(e))


@mcp.tool()
def clear_range(user_id: str, spreadsheet_id: str, range: str) -> str:
    """
    Clears all values in the specified range.
    'range' uses A1 notation e.g. 'Sheet1!A1:D10'.
    """
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        result = service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=range,
            body={}
        ).execute()
        return json.dumps({"clearedRange": result.get("clearedRange")})
    except HttpError as e:
        return create_error_response("API error during clear_range.", str(e))


@mcp.tool()
def find_and_replace(user_id: str, spreadsheet_id: str, find: str, replacement: str, sheet_id: int = 0) -> str:
    """
    Finds all occurrences of 'find' and replaces with 'replacement' across the sheet.
    'sheet_id' is the integer sheet index (default 0 = first sheet).
    """
    service = get_sheets_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with Google Sheets.")
    try:
        body = {
            "requests": [{
                "findReplace": {
                    "find": find,
                    "replacement": replacement,
                    "allSheets": False,
                    "sheetId": sheet_id,
                }
            }]
        }
        result = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        find_replace_result = result.get("replies", [{}])[0].get("findReplace", {})
        return json.dumps({
            "occurrencesChanged": find_replace_result.get("occurrencesChanged", 0)
        })
    except HttpError as e:
        return create_error_response("API error during find_and_replace.", str(e))


if __name__ == "__main__":
    print("--- Google Sheets MCP Server starting up... ---")
    mcp.run(transport="sse", host="0.0.0.0", port=8004)