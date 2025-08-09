# manage_channels.py
import os
import libsql
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_AUTH_TOKEN = os.getenv("DB_AUTH_TOKEN")

def get_db_connection():
    return libsql.connect(database=DB_URL, auth_token=DB_AUTH_TOKEN)

def list_channels():
    print("\n--- Canales en la Base de Datos ---")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT channel_name, channel_id, category FROM channels")
    channels = cursor.fetchall()
    conn.close()
    if not channels:
        print("No hay canales.")
    else:
        for channel in channels:
            print(f"- Nombre: {channel[0]}, ID: {channel[1]}, Categoría: {channel[2]}")
    print("---------------------------------")

def add_channel():
    channel_name = input("Introduce el nombre del canal: ")
    channel_id = input("Introduce el ID del canal (ej: UC_...): ")
    category = input("Introduce la categoría (ej: Noticias): ")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO channels (channel_name, channel_id, category) VALUES (?, ?, ?)",
            (channel_name, channel_id, category)
        )
        conn.commit()
        print(f"\n¡Canal '{channel_name}' añadido con éxito!")
    except libsql.IntegrityError:
        print("\nError: Ese ID de canal ya existe en la base de datos.")
    except Exception as e:
        print(f"\nOcurrió un error: {e}")
    finally:
        conn.close()

def delete_channel():
    channel_id = input("Introduce el ID del canal que quieres borrar: ")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    
    if cursor.rows_affected > 0:
        print(f"\n¡Canal con ID '{channel_id}' borrado con éxito!")
    else:
        print(f"\nNo se encontró ningún canal con el ID '{channel_id}'.")
    conn.close()

def main():
    while True:
        print("\n--- Panel de Control de Canales ---")
        print("1. Ver todos los canales")
        print("2. Añadir un nuevo canal")
        print("3. Borrar un canal")
        print("4. Salir")
        choice = input("Elige una opción: ")

        if choice == '1':
            list_channels()
        elif choice == '2':
            add_channel()
        elif choice == '3':
            delete_channel()
        elif choice == '4':
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")

if __name__ == "__main__":
    main()