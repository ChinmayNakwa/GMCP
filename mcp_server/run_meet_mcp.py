import sys
import os
import json
from fastmcp import FastMCP
from google.apps import meet_v2
from google_auth.services.google_meet import get_meet_service

print("--- run_meet_mcp.py starting up inside container ---", file=sys.stderr)
print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
print(f"Python path: {sys.path}", file=sys.stderr)

mcp = FastMCP("Meet")

def create_error_response(message: str, details: str = None) -> str:
    error_obj = {"error": message}
    if details:
        error_obj["details"] = details
    return json.dumps(error_obj)

@mcp.tool()
def create_meet_space(user_id: str):
    """Creates a new Google Meet space and returns its URI and name."""
    service = get_meet_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with meet")
    try: 
        request = meet_v2.CreateSpaceRequest()
        response = service.create_space(request=request)

        return json.dumps({"meeting_uri": response.meeting_uri, "name": response.name})
    except Exception as e:
        return create_error_response("An API error occured during create meet space.", str(e))

@mcp.tool()
def get_meet_space(user_id: str, name: str) -> str:
    """Retrieves the details of a Google Meet space by its name (resource ID)."""
    service = get_meet_service(user_id)
    if not service:
        return create_error_response("Failed to authenticate with meet")
    try:
        request = meet_v2.GetSpaceRequest(
            name=name,
        )
        response = service.get_space(request=request)
        return meet_v2.Space.to_json(response)
    except Exception as e:
        return create_error_response("An API error occured during searching for meet space.", str(e))
    
# @mcp.tool()
# def update_meet_space(name: str, access_type: Union[str, int]) -> str:
#     """
#     Updates a Google Meet space's access type.
#     'name' is the resource ID of the space (e.g., 'spaces/xxx').
#     'access_type' can be a string ('OPEN', 'RESTRICTED', 'TRUSTED') or a number (1, 2, 3).
#     """
#     service = get_meet_service()
#     if not service:
#         return create_error_response("Failed to authenticate with meet")

#     # Hardcoded map for flexibility. Handles strings and numbers.
#     ACCESS_TYPE_MAP = {
#         "OPEN": meet_v2.SpaceConfig.AccessType.OPEN,
#         "1": meet_v2.SpaceConfig.AccessType.OPEN,
#         "RESTRICTED": meet_v2.SpaceConfig.AccessType.RESTRICTED,
#         "2": meet_v2.SpaceConfig.AccessType.RESTRICTED,
#         "TRUSTED": meet_v2.SpaceConfig.AccessType.TRUSTED,
#         "3": meet_v2.SpaceConfig.AccessType.TRUSTED,
#     }

#     # Normalize input to an uppercase string to use the map
#     normalized_input = str(access_type).upper()
#     access_type_enum = ACCESS_TYPE_MAP.get(normalized_input)

#     # If the input is not valid, return a helpful error.
#     if access_type_enum is None:
#         valid_options = "'OPEN' (1), 'RESTRICTED' (2), 'TRUSTED' (3)"
#         return create_error_response(
#             f"Invalid access_type: '{access_type}'",
#             f"Please use one of the following options: {valid_options}."
#         )

#     try:
#         space_update = meet_v2.Space(
#             name=name,
#             config=meet_v2.SpaceConfig(
#                 access_type=access_type_enum
#             )
#         )

#         update_mask = field_mask_pb2.FieldMask(
#             paths=["config.access_type"]
#         )

#         request = meet_v2.UpdateSpaceRequest(
#             space=space_update,
#             update_mask=update_mask,
#         )

#         response = service.update_space(request=request)
#         return meet_v2.Space.to_json(response)
    
#     except Exception as e:
#         return create_error_response("An API error occured during updating the meet space.", str(e))


# @mcp.tool()
# def get_conference_record(name: str) -> str:
#     service = get_meet_service()
#     if not service:
#         return create_error_response("Failed to authenticate with meet")
#     try: 
#         request = meet_v2.GetConferenceRecordRequest(
#             name=name,
#         )
#         response = service.get_conference_record(request=request)
#         return meet_v2.ConferenceRecord.to_json(response)
#     except Exception as e:
#         return create_error_response("An API error occured during getting conference name.", str(e))

if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8003)
