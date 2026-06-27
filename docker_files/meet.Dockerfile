FROM python:3.12-slim
WORKDIR /app

COPY models/ /app/models/
COPY auth/ /app/auth/
COPY .env .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# This will show us if the paths in the COPY commands are correct.
RUN ls -R

# Copy the Meet tool server script
COPY mcp_server/run_meet_mcp.py .

# Copy the entire google_auth package
COPY google_auth/ /app/google_auth/

CMD ["python", "run_meet_mcp.py"]