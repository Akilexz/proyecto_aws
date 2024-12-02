import psycopg2
from config import RDS_HOST, RDS_DB, RDS_USER, RDS_PASSWORD

def get_connection():
    return psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DB,
        user=RDS_USER,
        password=RDS_PASSWORD
    )

def execute_query(query, params=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    if fetch:
        result = cursor.fetchall()
        conn.close()
        return result
    conn.commit()
    conn.close()
