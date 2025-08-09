# add_column.py
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

    print("Añadiendo la columna 'channel_name' a la tabla 'analysis_jobs'...")
    # El comando fallará si la columna ya existe, lo cual está bien.
    cursor.execute("ALTER TABLE analysis_jobs ADD COLUMN channel_name TEXT")
    conn.commit()
    print("Columna 'channel_name' añadida con éxito.")

except Exception as e:
    # Si la columna ya existe, la base de datos dará un error. Lo capturamos.
    if "duplicate column name" in str(e):
        print("La columna 'channel_name' ya existe. No se necesita hacer nada.")
    else:
        print(f"Ocurrió un error inesperado: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()