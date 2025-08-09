# migrate.py
import sqlite3
import libsql
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_AUTH_TOKEN = os.getenv("DB_AUTH_TOKEN")
LOCAL_DB_FILE = 'channels.db'

if not all([DB_URL, DB_AUTH_TOKEN]):
    print("Error: Revisa que DB_URL y DB_AUTH_TOKEN están en tu archivo .env")
    exit()

def migrate_data():
    try:
        local_conn = sqlite3.connect(LOCAL_DB_FILE); local_conn.row_factory = sqlite3.Row; cursor = local_conn.cursor()
        print("Conectado a la DB local.")
        cursor.execute("SELECT channel_id, channel_name, category FROM channels"); channels = cursor.fetchall(); local_conn.close()
        print(f"Se encontraron {len(channels)} canales para migrar.")
        if not channels: return

        turso_conn = libsql.connect(database=DB_URL, auth_token=DB_AUTH_TOKEN); turso_cursor = turso_conn.cursor()
        print("Conectado a Turso.")
        turso_cursor.execute("CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, channel_id TEXT UNIQUE, channel_name TEXT, category TEXT)")
        print("Tabla 'channels' asegurada en Turso.")

        for channel in channels:
            try: turso_cursor.execute("INSERT INTO channels (channel_id, channel_name, category) VALUES (?, ?, ?)", (channel['channel_id'], channel['channel_name'], channel['category']))
            except libsql.IntegrityError: print(f"El canal '{channel['channel_name']}' ya existe en Turso. Saltando.")
        
        turso_conn.commit(); turso_conn.close()
        print("\n¡Migración completada con éxito!")
    except Exception as e: print(f"\nOcurrió un error: {e}")

if __name__ == '__main__': migrate_data()