
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Разрешаем CORS для локального фронтенда (file://, localhost, 127.0.0.1)
CORS(app)

DATA_FILE = "data.txt"


@app.route("/submit", methods=["POST", "OPTIONS"])
def submit():
    # Flask-CORS сам обрабатывает preflight OPTIONS,
    # но оставим явную проверку на всякий случай
    if request.method == "OPTIONS":
        return ("", 204)

    data = request.get_json(silent=True) or {}
    text = data.get("text", "")

    # Дописываем текст в файл (каждый запрос — новая строка)
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

    return jsonify({"status": "ok", "received": text}), 200


if __name__ == "__main__":
    # host=0.0.0.0, чтобы сервер был доступен и с других устройств в сети
    app.run(host="0.0.0.0", port=5000, debug=True)
