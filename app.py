# app.py (Versión con Descarga de JSON)
import os
import uuid
import threading
import secrets
import json # ¡NUEVO! Para manejar el formato JSON
from flask import Flask, render_template, redirect, url_for, jsonify, request, flash, Response
from dotenv import load_dotenv
from datetime import datetime

import youtube_logic
import llm_analyzer

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(16))

# --- Lógica de la Tarea en Segundo Plano ---
def run_analysis_task(job_id, channel_id):
    print(f"Iniciando análisis para el job_id: {job_id}")
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    try:
        # 1. Obtener datos de YouTube
        videos = youtube_logic.get_channel_videos_last_week(channel_id)
        if not videos:
            raise ValueError(f"No se encontraron videos recientes para el canal {channel_id}.")

        # ¡NUEVO! Convertimos los datos a un string JSON y los guardamos inmediatamente.
        json_data_string = json.dumps(videos, indent=2, ensure_ascii=False)
        cursor.execute("UPDATE analysis_jobs SET raw_json_data = ? WHERE id = ?", (json_data_string, job_id))
        db.commit()

        # 2. Analizar con el LLM
        analysis_result = llm_analyzer.analyze_with_openrouter(youtube_logic.GROK_ECONOMIC_CONCERN, videos)

        # 3. Guardar el resultado final en la base de datos
        cursor.execute("UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?", ("completed", analysis_result, job_id))
        db.commit()
        print(f"Job {job_id} completado con éxito.")

    except Exception as e:
        print(f"Error en el job {job_id}: {e}")
        cursor.execute("UPDATE analysis_jobs SET status = ?, result = ? WHERE id = ?", ("failed", str(e), job_id))
        db.commit()
    finally:
        db.close()

# --- Rutas de la Aplicación Web ---
@app.route('/')
def index():
    channels = youtube_logic.get_all_saved_channels()
    return render_template('index.html', channels=channels)

# ... (Las rutas /add y /delete se quedan igual) ...
@app.route('/add', methods=['GET', 'POST'])
def add_channel():
    if request.method == 'POST':
        name = request.form['channel_name']; channel_id = request.form['channel_id']
        success, message = youtube_logic.add_channel_to_db(name, channel_id)
        flash(message); return redirect(url_for('index'))
    return render_template('add_channel.html')

@app.route('/delete/<channel_id>', methods=['POST'])
def delete_channel(channel_id):
    success, message = youtube_logic.delete_channel_from_db(channel_id)
    flash(message); return redirect(url_for('index'))

# --- Rutas de Análisis ---
# ... (start_analysis, show_result, get_status, historial se quedan casi igual) ...
@app.route('/analizar/<channel_id>')
def start_analysis(channel_id):
    job_id = str(uuid.uuid4())
    channel_name = youtube_logic.get_channel_name_from_db(channel_id) or "Desconocido"
    db = youtube_logic.get_db_connection(); cursor = db.cursor()
    cursor.execute("INSERT INTO analysis_jobs (id, status, channel_name) VALUES (?, ?, ?)",(job_id, "pending", channel_name))
    db.commit(); db.close()
    thread = threading.Thread(target=run_analysis_task, args=(job_id, channel_id)); thread.start()
    return redirect(url_for('show_result', job_id=job_id))

@app.route('/resultado/<job_id>')
def show_result(job_id):
    db = youtube_logic.get_db_connection(); cursor = db.cursor()
    cursor.execute("SELECT channel_name FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone(); db.close()
    channel_name = job[0] if job else "Desconocido"
    return render_template('resultado.html', job_id=job_id, channel_name=channel_name)

@app.route('/status/<job_id>')
def get_status(job_id):
    db = youtube_logic.get_db_connection(); cursor = db.cursor()
    cursor.execute("SELECT status, result FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone(); db.close()
    if job: return jsonify({"status": job[0], "result": job[1]})
    else: return jsonify({"status": "not_found"}), 404

@app.route('/historial')
def historial():
    db = youtube_logic.get_db_connection(); cursor = db.cursor()
    cursor.execute("SELECT id, channel_name, status, created_at FROM analysis_jobs ORDER BY created_at DESC")
    jobs = cursor.fetchall(); db.close()
    return render_template('historial.html', jobs=jobs)

# --- ¡NUEVA RUTA PARA DESCARGAR EL JSON! ---
@app.route('/download/<job_id>')
def download_json(job_id):
    db = youtube_logic.get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT raw_json_data, channel_name FROM analysis_jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    db.close()

    if job and job[0]:
        json_data = job[0]
        channel_name = job[1].replace(" ", "_")
        filename = f"datos_{channel_name}_{job_id[:8]}.json"
        
        return Response(
            json_data,
            mimetype="application/json",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    else:
        flash("No se encontraron datos JSON para descargar para este análisis.")
        return redirect(url_for('historial'))

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)