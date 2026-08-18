from flask import Flask, jsonify, render_template

app = Flask(__name__)

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "AI YEREL GPT"
    })

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
