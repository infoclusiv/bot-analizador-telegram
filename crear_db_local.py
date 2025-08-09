# crear_db_local.py
import sqlite3

DB_FILE = 'channels.db'
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Crear tabla
cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE NOT NULL,
        channel_name TEXT NOT NULL,
        category TEXT DEFAULT 'Noticias'
    )
""")

# Insertar un canal de ejemplo (cámbialo si quieres)
try:
    cursor.execute(
        "INSERT INTO channels (channel_id, channel_name, category) VALUES (?, ?, ?)",
        ('UC-y-1_xHnFxI5aYgZ2vYm5Q', 'VisualPolitik', 'Análisis')
    )
    print("Canal de ejemplo 'VisualPolitik' insertado.")
except sqlite3.IntegrityError:
    print("El canal de ejemplo 'VisualPolitik' ya existe.")

conn.commit()
conn.close()
print(f"Base de datos local '{DB_FILE}' creada/actualizada con éxito.")