# add_json_column.py
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

    print("Añadiendo la columna 'raw_json_data' a la tabla 'analysis_jobs'...")
    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN raw_json_data TEXT")
    conn.commit()
    print("Columna 'raw_json_data' añadida con éxito.")

except Exception as e:
    if "duplicate column name" in str(e):
        print("La columna 'raw_json_data' ya existe. No se necesita hacer nada.")
    else:
        print(f"Ocurrió un error inesperado: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()