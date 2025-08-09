# app.py
import os
import uuid
import threading
from flask import Flask, render_template, redirect, url_for, jsonify
from dotenv import load_dotenv

# Importamos nuestra lógica de siempre
import youtube_logic
import llm_analyzer

load_dotenv()

app = Flask(__name__)

# --- Lógica de la Tarea en Segundo Plano ---
def run_analysis_task(job_id, channel_id):
    """
    Esta función se ejecuta en un hilo separado.
    Realiza el análisis y actualiza la base de datos con el resultado.
    """
    print(f"Iniciando análisis para el job_id: {job_id}")
    try:
        # 1. Obtener datos de YouTube
        videos = youtube_logic.get_channel_videos_last_week(channel_id)
        if not videos:
            raise ValueError(f"No se encontraron videos recientes para el canal {channel_id}.")

        # 2. Analizar con el LLM
        analysis_result = llm_analyzer.analyze_with_openrouter(youtube_logic.GROK_ECONOMIC_CONCERN, videos)

        # 3. Guardar el resultado en la base de datos
        db = youtube_logic.get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?",
            ("completed", analysis_result, job_id)
        )
        db.commit()
        db.close()
        print(f"Job {job_id} completado con éxito.")

    except Exception as e:
        print(f"Error en el job {job_id}: {e}")
        # Guardar el error en la base de datos
        db = youtube_logic.get_db_connection()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?",
            ("failed", str(e), job_id)
        )
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
    job_id = str(uuid.uuid4()) # Crea un ID único para el trabajo

    # Registra el nuevo trabajo en la base de datos
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO analysis_jobs (id, status) VALUES (?, ?)",
        (job_id, "pending")
    )
    db.commit()
    db.close()

    # Inicia el análisis en un hilo de fondo
    thread = threading.Thread(target=run_analysis_task, args=(job_id, channel_id))
    thread.start()

    # Redirige al usuario a la página de resultados
    return redirect(url_for('show_result', job_id=job_id))

@app.route('/resultado/<job_id>')
def show_result(job_id):
    """Muestra la página de espera/resultados."""
    return render_template('resultado.html', job_id=job_id)

@app.route('/status/<job_id>')
def get_status(job_id):
    """API interna para que la página de resultados pregunte por el estado."""
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT status, result FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    db.close()

    if job:
        return jsonify({"status": job[0], "result": job[1]})
    else:
        return jsonify({"status": "not_found"}), 404

if __name__ == "__main__":
    # Esta parte es para que funcione en Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)