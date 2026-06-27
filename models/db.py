import psycopg2, json, os

def get_conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

def save_token(user_id: str, service: str, token_data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_tokens (user_id, service, token_json)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, service) DO UPDATE SET token_json = EXCLUDED.token_json
    """, (user_id, service, json.dumps(token_data)))
    conn.commit()

def load_token(user_id: str, service: str):
    cur = get_conn().cursor()
    cur.execute("SELECT token_json FROM user_tokens WHERE user_id=%s AND service=%s", (user_id, service))
    row = cur.fetchone()
    return json.loads(row[0]) if row else None