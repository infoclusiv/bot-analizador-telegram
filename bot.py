# bot.py (versión final y mejorada)
import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

import youtube_logic
import llm_analyzer

# --- CONFIGURACIÓN DEL SERVIDOR WEB (para Render) ---
# Creamos una mini aplicación web con Flask
app = Flask(__name__)

@app.route('/')
def health_check():
    """Esta ruta es para que Render y UptimeRobot sepan que el bot está vivo."""
    return "Bot is alive!"

def run_flask_app():
    """Función para correr Flask en un puerto que Render pueda detectar."""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# -----------------------------------------------------


# Cargar variables de entorno
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- LÓGICA DEL BOT DE TELEGRAM (sin cambios) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Comando /start recibido")
    try:
        channels = youtube_logic.get_all_saved_channels()
        if not channels:
            await update.message.reply_text("No se encontraron canales en la base de datos.")
            return
        
        keyboard = [[InlineKeyboardButton(ch['channel_name'], callback_data=ch['channel_id'])] for ch in channels]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Hola! Selecciona un canal para analizar:', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error al obtener canales: {e}")
        await update.message.reply_text(f"Error al conectar con la base de datos: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    channel_id = query.data
    channel_name = youtube_logic.get_channel_name_from_db(channel_id) or "Desconocido"
    logger.info(f"Iniciando análisis para el canal: {channel_name} ({channel_id})")
    
    await query.edit_message_text(text=f"Analizando '{channel_name}'... \nEsto puede tardar hasta 2 minutos.")

    try:
        videos = youtube_logic.get_channel_videos_last_week(channel_id)
        if not videos:
            await query.edit_message_text(text=f"No se encontraron videos recientes para '{channel_name}'.")
            return

        analysis_result = llm_analyzer.analyze_with_openrouter(youtube_logic.GROK_ECONOMIC_CONCERN, videos)
        await query.edit_message_text(text=analysis_result)
    except Exception as e:
        logger.error(f"Error en el flujo de análisis: {e}", exc_info=True)
        await query.edit_message_text(text=f"Lo siento, ocurrió un error. Detalles: {e}")

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN no encontrado en .env")
        return

    # --- INICIAR EL SERVIDOR WEB EN UN HILO SEPARADO ---
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()
    # --------------------------------------------------

    # Iniciar el bot de Telegram
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Iniciando el bot de Telegram...")
    application.run_polling()

if __name__ == '__main__':
    main()