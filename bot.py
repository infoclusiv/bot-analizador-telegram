# bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

import youtube_logic
import llm_analyzer

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Comando /start recibido")
    try:
        channels = youtube_logic.get_all_saved_channels()
        if not channels:
            await update.message.reply_text("No se encontraron canales en la base de datos en la nube. ¿Ejecutaste el script de migración?")
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
    
    await query.edit_message_text(text=f"Analizando '{channel_name}'... \nEsto puede tardar hasta 2 minutos. Por favor, espera.")

    try:
        videos = youtube_logic.get_channel_videos_last_week(channel_id)
        if not videos:
            await query.edit_message_text(text=f"No se encontraron videos recientes (últimos 3 días) para '{channel_name}'.")
            return

        analysis_result = llm_analyzer.analyze_with_openrouter(youtube_logic.GROK_ECONOMIC_CONCERN, videos)
        await query.edit_message_text(text=analysis_result)
    except Exception as e:
        logger.error(f"Error en el flujo de análisis: {e}", exc_info=True)
        await query.edit_message_text(text=f"Lo siento, ocurrió un error inesperado. Detalles: {e}")

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Error: TELEGRAM_BOT_TOKEN no encontrado en .env")
        return
        
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Iniciando el bot...")
    application.run_polling()

if __name__ == '__main__':
    main()