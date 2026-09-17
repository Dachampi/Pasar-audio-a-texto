# usar este comando para inicar py app.py


from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import whisper
import os
import uuid
import torch
import threading
import time

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

TASKS = {}
TASK_LOCK = threading.Lock()

device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_NAME = "small"

print(f"Cargando modelo Whisper: {MODEL_NAME}")
print(f"Dispositivo detectado: {device}")

model = whisper.load_model(MODEL_NAME, device=device)

def update_task(task_id, progress=None, status=None, transcription=None, filename=None, error=None):
    with TASK_LOCK:
        if task_id not in TASKS:
            TASKS[task_id] = {}

        if progress is not None:
            TASKS[task_id]["progress"] = progress

        if status is not None:
            TASKS[task_id]["status"] = status

        if transcription is not None:
            TASKS[task_id]["transcription"] = transcription

        if filename is not None:
            TASKS[task_id]["filename"] = filename

        if error is not None:
            TASKS[task_id]["error"] = error


def simulate_progress(task_id, stop_event):
    visual_steps = [
        (12, "Archivo recibido correctamente"),
        (20, "Validando formato de audio"),
        (30, "Preparando audio con FFmpeg"),
        (42, "Inicializando motor Whisper"),
        (55, "Analizando voz y silencios"),
        (68, "Detectando idioma y contexto"),
        (78, "Generando transcripción"),
        (88, "Organizando el texto"),
        (94, "Preparando resultado final")
    ]

    current_progress = 5

    for target, message in visual_steps:
        while current_progress < target and not stop_event.is_set():
            current_progress += 1
            update_task(task_id, progress=current_progress, status=message)
            time.sleep(0.35)

        if stop_event.is_set():
            break


def transcribe_audio(task_id, filepath, original_filename, language):
    stop_event = threading.Event()

    try:
        update_task(
            task_id,
            progress=5,
            status="Iniciando proceso local",
            filename=original_filename,
            transcription=""
        )

        progress_thread = threading.Thread(
            target=simulate_progress,
            args=(task_id, stop_event)
        )
        progress_thread.start()

        options = {
            "fp16": device == "cuda"
        }

        if language:
            options["language"] = language

        result = model.transcribe(filepath, **options)

        stop_event.set()
        progress_thread.join()

        update_task(task_id, progress=97, status="Limpiando y preparando texto")
        time.sleep(0.5)

        transcription = result.get("text", "").strip()

        update_task(
            task_id,
            progress=100,
            status="Transcripción completada",
            transcription=transcription
        )

        try:
            os.remove(filepath)
        except:
            pass

    except Exception as e:
        stop_event.set()
        update_task(
            task_id,
            progress=100,
            status="Ocurrió un error durante la transcripción",
            error=str(e)
        )


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        device=device,
        model_name=MODEL_NAME
    )


@app.route("/start", methods=["POST"])
def start_transcription():
    audio = request.files.get("audio")
    language = request.form.get("language")

    if not audio or not audio.filename:
        return jsonify({
            "success": False,
            "message": "No se recibió ningún archivo de audio."
        }), 400

    task_id = str(uuid.uuid4())

    safe_name = secure_filename(audio.filename)
    unique_name = f"{task_id}_{safe_name}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)

    audio.save(filepath)

    update_task(
        task_id,
        progress=1,
        status="Archivo enviado al servidor local",
        filename=audio.filename,
        transcription=""
    )

    thread = threading.Thread(
        target=transcribe_audio,
        args=(task_id, filepath, audio.filename, language)
    )
    thread.start()

    return jsonify({
        "success": True,
        "task_id": task_id
    })


@app.route("/progress/<task_id>", methods=["GET"])
def get_progress(task_id):
    with TASK_LOCK:
        task = TASKS.get(task_id)

    if not task:
        return jsonify({
            "success": False,
            "message": "No se encontró el proceso."
        }), 404

    return jsonify({
        "success": True,
        "progress": task.get("progress", 0),
        "status": task.get("status", "Esperando"),
        "transcription": task.get("transcription", ""),
        "filename": task.get("filename", ""),
        "error": task.get("error", "")
    })


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)