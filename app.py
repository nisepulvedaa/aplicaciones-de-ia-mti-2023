# Archivo: app.py

from flask import Flask, render_template, request, jsonify
from app.multiagent_rag import run_multiagent

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/preguntar", methods=["POST"])
def preguntar():
    data = request.get_json()
    pregunta = data.get("pregunta", "")

    if not pregunta:
        return jsonify({"error": "No se recibió una pregunta."}), 400

    resultado = run_multiagent(pregunta)

    return jsonify({
        "respuesta": resultado["respuesta"],
        "hallucination": resultado["hallucination"]
    })

if __name__ == "__main__":
    app.run(debug=True)