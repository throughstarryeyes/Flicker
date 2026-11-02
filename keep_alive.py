from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.get("/")
def home():
    return "Flicker is awake!"

@app.get("/health")
def health():
    return "ok"

def _run():
    # Replit likes 0.0.0.0 and port 8080; fall back to $PORT if provided
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)

def keep_alive():
    t = Thread(target=_run, daemon=True)
    t.start()