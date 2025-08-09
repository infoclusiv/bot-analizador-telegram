# youtube_logic.py (Versión Corregida)
import os
import libsql
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
DB_URL = os.getenv("DB_URL")
DB_AUTH_TOKEN = os.getenv("DB_AUTH_TOKEN")

# El prompt que usaremos para el análisis
GROK_ECONOMIC_CONCERN = """Analyze the provided JSON data and tell me, based on the number of views of the videos, what could be the topic of greatest concern for Americans regarding their economy? Use the data contained in the file. Also, give me the titles, links and number of views of the videos related to that topic. Sort the videos by views in descending order. Present the final answer in Spanish."""

youtube = None
if YOUTUBE_API_KEY:
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    except Exception as e:
        print(f"Error inicializando la API de YouTube: {e}")
else:
    print("Error: YOUTUBE_API_KEY no encontrada. Asegúrate de que está en el archivo .env")

def get_db_connection():
    """Se conecta a la base de datos de Turso en la nube."""
    if not all([DB_URL, DB_AUTH_TOKEN]):
        raise ValueError("DB_URL y DB_AUTH_TOKEN deben estar configurados en el archivo .env")
    conn = libsql.connect(database=DB_URL, auth_token=DB_AUTH_TOKEN)
    # LA LÍNEA QUE DABA EL ERROR HA SIDO ELIMINADA DE AQUÍ
    return conn

def get_all_saved_channels():
    """Obtiene todos los canales de la base de datos de Turso."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT channel_id, channel_name FROM channels ORDER BY channel_name')
    channels_raw = cursor.fetchall()
    conn.close()
    # AJUSTE: Convertimos manualmente los resultados a diccionarios
    return [{'channel_id': row[0], 'channel_name': row[1]} for row in channels_raw]

def get_channel_name_from_db(channel_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT channel_name FROM channels WHERE channel_id = ?', (channel_id,))
    channel = cursor.fetchone()
    conn.close()
    # AJUSTE: Accedemos al resultado por su posición (0) en lugar de por nombre
    return channel[0] if channel else None

def get_channel_videos_last_week(channel_id, include_shorts=False):
    """Obtiene los videos de un canal de los últimos 3 días."""
    if not youtube:
        raise ConnectionError("La API de YouTube no está inicializada.")
        
    three_days_ago = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat().replace('+00:00', 'Z')
    videos_data = []
    
    try:
        search_response = youtube.search().list(
            part='id', channelId=channel_id, publishedAfter=three_days_ago,
            type='video', order='date', maxResults=50
        ).execute()
        
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        if not video_ids: return []
        
        video_details_response = youtube.videos().list(
            part='snippet,statistics', id=','.join(video_ids)
        ).execute()
        
        for item in video_details_response.get('items', []):
            videos_data.append({
                'title': item['snippet']['title'],
                'views': int(item['statistics'].get('viewCount', 0)),
                'url': f"https://www.youtube.com/watch?v={item['id']}"
            })
    except Exception as e:
        print(f"Error al obtener videos de YouTube para {channel_id}: {e}")
        return []
        
    return videos_data

def add_channel_to_db(channel_name, channel_id, category="Noticias"):
    """Añade un nuevo canal a la base de datos. Devuelve (éxito, mensaje)."""
    if not channel_name or not channel_id:
        return (False, "El nombre y el ID del canal no pueden estar vacíos.")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO channels (channel_name, channel_id, category) VALUES (?, ?, ?)",
            (channel_name, channel_id, category)
        )
        conn.commit()
        return (True, f"¡Canal '{channel_name}' añadido con éxito!")
    except libsql.IntegrityError:
        return (False, "Error: Ese ID de canal ya existe en la base de datos.")
    except Exception as e:
        return (False, f"Ocurrió un error inesperado: {e}")
    finally:
        conn.close()

def delete_channel_from_db(channel_id):
    """Borra un canal de la base de datos por su ID. Devuelve (éxito, mensaje)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    
    success = cursor.rows_affected > 0
    conn.close()
    
    if success:
        return (True, f"¡Canal con ID '{channel_id}' borrado con éxito!")
    else:
        return (False, f"No se encontró ningún canal con el ID '{channel_id}'.")