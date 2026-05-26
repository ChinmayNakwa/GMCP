# Google Workspace MCP Tool Server

A standalone, runnable tool server that provides a complete set of functions for interacting with the Google Calendar, Meet and Gmail API. This server is built using the Model-Context-Protocol (`mcp`) library and is designed to be called by an external AI agent or orchestrator.

This server acts as the "hardware" or "limbs" of an AI agent, handling all the secure authentication and direct API calls to Google, while exposing a simple, clean interface.

## Features

- **Standalone & Executable:** Runs as a separate process, listening for tool call requests on standard I/O (`stdio`).
- **Secure Authentication:** Manages the entire Google OAuth 2.0 flow, including initial user login and subsequent token refreshes.
- **Robust Toolset:** Provides a comprehensive set of tools for calendar management.
- **JSON Interface:** Accepts and returns data in clean, easy-to-parse JSON format.


## Setup and Installation

### Prerequisites

- Python 3.10+
- A Google Account
- A Google Cloud Platform project with the Google Calendar/Meet/Mail API enabled.

### 1. Setup Google Cloud Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to `APIs & Services > Credentials`.
3. Click **+ CREATE CREDENTIALS** -> **OAuth client ID**.
4. Select **Desktop app** for the Application type.
5. Click **DOWNLOAD JSON** and rename the downloaded file to `credentials.json`.
6. Place this file inside a `credentials/` directory in the project root.

### 2. Install Dependencies

1. **Clone the repository and navigate into it.**

2. **Create and activate a virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On macOS/Linux
   # On Windows: .venv\Scripts\activate
   ```

3. **Install the required packages:**
   ```bash
   uv pip install -r requirements.txt
   ```
   *(Ensure `requirements.txt` contains `mcp`, `google-api-python-client`, `google-auth-oauthlib`, etc.)*

## How to Run the Server

You can run the tool server directly from your terminal.

```bash
python run_calendar_mcp.py
```

The server will start and print `Starting MCP server 'GoogleCalendar' with transport 'stdio'`.

The very first time you run a command that requires calendar access, the server will trigger the Google OAuth flow:
1. Your web browser will open.
2. You must log in and grant the requested permissions.
3. A `token.json` file will be created in the `credentials/` folder.

This is a one-time process. Subsequent runs will use the saved token.

## Docker Deployment

### How it Works

The `Dockerfile` defines the steps to create an image:
1. It starts from a base Python image.
2. It sets up a working directory and copies the `requirements.txt` file.
3. It installs all Python dependencies using uv.
4. It copies your application source code (`run_calendar_mcp.py`, `mcp_server/`, etc.).
5. **Crucially, it copies the `credentials/` folder (containing both `credentials.json` and your generated `token.json`) into the image.**
6. It exposes port 8000 and defines the command to start the MCP server.

### Building the Docker Image

From the project's root directory, run the following command to build the image:

```bash
docker build -t google-calendar-mcp .
```

### Running the Docker Container

Once the image is built, you can run it as a container:

```bash
docker run -p 8000:8000 --env-file .env google-calendar-mcp
```

- `-p 8000:8000`: Maps the container's port 8000 to your host's port 8000.
- `--env-file .env`: Securely passes the API keys from your local `.env` file into the container's environment.

## Claude Desktop Integration

Edit this in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "GoogleCalendar": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", "${PWD}/credentials:/app/credentials",
        "google-calendar-mcp"
      ]
    }
  }
}
```

This configuration allows Claude Desktop to interact with your Google Calendar through the MCP server running in Docker, with proper credential mounting for secure authentication.
