import logging
import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from flask_cors import CORS

# ---------- Конфигурация (можно переопределить через переменные окружения) ----------
DATA_FILE = os.getenv("DATA_FILE", "data.txt")
HOST      = os.getenv("HOST", "127.0.0.1")
PORT      = int(os.getenv("PORT", 5000))
DEBUG     = os.getenv("DEBUG", "1") == "1"

# ---------- Логирование ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("backend")

# ---------- Приложение ----------
app = Flask(__name__)
CORS(app)


def _file_meta() -> dict:
    """Метаданные файла — если он существует, иначе дефолтные значения."""
    try:
        stat = os.stat(DATA_FILE)
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }
    except FileNotFoundError:
        return {"exists": False, "size_bytes": 0, "modified": None}


# ---------- POST /submit : запись текста в data.txt ----------
@app.route("/submit", methods=["POST", "OPTIONS"])
def submit():
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    text = str(data.get("text", ""))

    if text.strip() == "":
        log.warning("POST /submit — пустой text")
        return jsonify({"status": "error", "message": "Поле 'text' пустое"}), 400

    try:
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError as exc:
        log.exception("Не удалось записать в %s", DATA_FILE)
        return jsonify({"status": "error", "message": str(exc)}), 500

    meta = _file_meta()
    log.info("POST /submit — записано %d символов, размер файла %d Б",
             len(text), meta["size_bytes"])

    return jsonify({
        "status": "ok",
        "received": text,
        "size_bytes": meta["size_bytes"],
    }), 200


# ---------- GET /read : чтение содержимого data.txt ----------
@app.route("/read", methods=["GET"])
def read_file():
    """
    Возвращает содержимое data.txt.
    Если файла ещё нет — content = "" (без 500-й ошибки).
    """
    content = ""
    meta = _file_meta()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        log.info("GET /read — прочитано %d символов", len(content))
    except FileNotFoundError:
        # требование методички: файла нет → пустая строка, а не 500
        log.warning("GET /read — файл %s не найден, возвращаю пустую строку", DATA_FILE)
    except OSError as exc:
        log.exception("GET /read — ошибка чтения %s", DATA_FILE)
        return jsonify({"status": "error", "message": str(exc)}), 500

    return jsonify({
        "status": "ok",
        "content": content,
        # бонусные поля — не ломают контракт из методички
        "lines": content.count("\n"),
        "size_bytes": meta["size_bytes"],
        "modified": meta["modified"],
    }), 200


# ---------- GET /health : проверка живучести ----------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "data_file": DATA_FILE,
        "file_exists": os.path.exists(DATA_FILE),
    }), 200


if __name__ == "__main__":
    log.info("Запуск сервера на http://%s:%d (data_file=%s)", HOST, PORT, DATA_FILE)
    app.run(host=HOST, port=PORT, debug=DEBUG)