# youtube_logic.py
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
GROK_ECONOMIC_CONCERN = """Analyze the provided JSON data and tell me, based on the number of views of the videos, what could be the topic of greatest concern for Americans regarding their economy? Use the data contained in the file. Also, give me the titles, links and number of views of the videos related to that topic. Present the final answer in Spanish."""

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
    conn.row_factory = libsql.Row
    return conn

def get_all_saved_channels():
    """Obtiene todos los canales de la base de datos de Turso."""
    conn = get_db_connection()
    channels_raw = conn.execute('SELECT channel_id, channel_name FROM channels ORDER BY channel_name').fetchall()
    conn.close()
    return [dict(row) for row in channels_raw]

def get_channel_name_from_db(channel_id):
    conn = get_db_connection()
    channel = conn.execute('SELECT channel_name FROM channels WHERE channel_id = ?', (channel_id,)).fetchone()
    conn.close()
    return channel['channel_name'] if channel else None

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