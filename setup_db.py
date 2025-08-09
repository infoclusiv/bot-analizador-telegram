# setup_db.py
import os
import libsql
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_AUTH_TOKEN = os.getenv("DB_AUTH_TOKEN")

if not all([DB_URL, DB_AUTH_TOKEN]):
    print("Error: Revisa que DB_URL y DB_AUTH_TOKEN están en tu archivo .env")
    exit()

try:
    print("Conectando a la base de datos de Turso...")
    conn = libsql.connect(database=DB_URL, auth_token=DB_AUTH_TOKEN)
    cursor = conn.cursor()
    print("Conexión exitosa.")

    print("Creando la tabla 'analysis_jobs' si no existe...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    print("Tabla 'analysis_jobs' asegurada con éxito.")

    conn.close()

except Exception as e:
    print(f"Ocurrió un error: {e}")