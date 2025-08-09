# app.py (Versión con Historial)
import os
import uuid
import threading
from flask import Flask, render_template, redirect, url_for, jsonify
from dotenv import load_dotenv
from datetime import datetime

# Importamos nuestra lógica de siempre
import youtube_logic
import llm_analyzer

load_dotenv()

app = Flask(__name__)

# --- Lógica de la Tarea en Segundo Plano (sin cambios) ---
def run_analysis_task(job_id, channel_id):
    print(f"Iniciando análisis para el job_id: {job_id}")
    try:
        videos = youtube_logic.get_channel_videos_last_week(channel_id)
        if not videos:
            raise ValueError(f"No se encontraron videos recientes para el canal {channel_id}.")
        analysis_result = llm_analyzer.analyze_with_openrouter(youtube_logic.GROK_ECONOMIC_CONCERN, videos)
        db = youtube_logic.get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?", ("completed", analysis_result, job_id))
        db.commit()
        db.close()
        print(f"Job {job_id} completado con éxito.")
    except Exception as e:
        print(f"Error en el job {job_id}: {e}")
        db = youtube_logic.get_db_connection()
        cursor = db.cursor()
        cursor.execute("UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?", ("failed", str(e), job_id))
        db.commit()
        db.close()

# --- Rutas de la Aplicación Web ---
@app.route('/')
def index():
    """Página principal que muestra la lista de canales."""
    channels = youtube_logic.get_all_saved_channels()
    return render_template('index.html', channels=channels)

@app.route('/analizar/<channel_id>')
def start_analysis(channel_id):
    """Inicia un nuevo trabajo de análisis y redirige a la página de resultados."""
    job_id = str(uuid.uuid4())
    
    # ¡NUEVO! Obtenemos el nombre del canal para guardarlo en el historial
    channel_name = youtube_logic.get_channel_name_from_db(channel_id) or "Desconocido"

    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    # ¡MODIFICADO! Añadimos el channel_name al registrar el trabajo
    cursor.execute(
        "INSERT INTO analysis_jobs (id, status, channel_name) VALUES (?, ?, ?)",
        (job_id, "pending", channel_name)
    )
    db.commit()
    db.close()

    thread = threading.Thread(target=run_analysis_task, args=(job_id, channel_id))
    thread.start()

    return redirect(url_for('show_result', job_id=job_id))

@app.route('/resultado/<job_id>')
def show_result(job_id):
    """Muestra la página de espera/resultados."""
    # ¡NUEVO! Obtenemos el nombre del canal para mostrarlo en la página
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT channel_name FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    db.close()
    channel_name = job[0] if job else "Desconocido"
    return render_template('resultado.html', job_id=job_id, channel_name=channel_name)

@app.route('/status/<job_id>')
def get_status(job_id):
    """API interna para que la página de resultados pregunte por el estado."""
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT status, result FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    db.close()
    if job: return jsonify({"status": job[0], "result": job[1]})
    else: return jsonify({"status": "not_found"}), 404

# --- ¡NUEVA RUTA PARA EL HISTORIAL! ---
@app.route('/historial')
def historial():
    """Muestra una lista de todos los análisis realizados."""
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    # Ordenamos por fecha para ver los más recientes primero
    cursor.execute("SELECT id, channel_name, status, created_at FROM analysis_jobs ORDER BY created_at DESC")
    jobs = cursor.fetchall()
    db.close()
    return render_template('historial.html', jobs=jobs)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)