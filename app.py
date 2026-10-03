from pathlib import Path
import subprocess
import sys

from flask import Flask, request, jsonify
from flask import send_file

app = Flask(__name__)
APP_DIR = Path(__file__).resolve().parent
INPUT_DIR = APP_DIR / "Input"
OUTPUT_FILE = APP_DIR / "Output" / "Final.xlsx"

@app.route("/test")
def test():
    return "Flask is working"


@app.route("/", methods=["GET"])
def index():
    return """
    <!doctype html>
    <html lang="en">
      <head><meta charset="utf-8"><title>Generate quote</title></head>
      <body>
        <h1>Generate quote</h1>
        <form action="/generate" method="post" enctype="multipart/form-data">
          <label>Services PDF <input type="file" name="services" accept=".pdf" required></label>
          <br>
          <label>Standard spreadsheet <input type="file" name="standard" accept=".xlsx" required></label>
          <br>
          <button type="submit">Generate</button>
        </form>
      </body>
    </html>
    """

@app.route("/generate", methods=["POST"])
def generate():
    services = request.files.get("services")
    standard = request.files.get("standard")
    if services is None or standard is None:
        return jsonify({"error": "Upload both a services PDF and a standard spreadsheet."}), 400

    INPUT_DIR.mkdir(exist_ok=True)
    services_path = INPUT_DIR / "Services.pdf"
    standard_path = INPUT_DIR / "Standard.xlsx"
    services.save(services_path)
    standard.save(standard_path)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    result = subprocess.run(
        [
            sys.executable,
            str(APP_DIR / "generate_final.py"),
            str(services_path),
            str(standard_path),
            str(OUTPUT_FILE),
        ],
        cwd=APP_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return jsonify({
            "error": "Quote generation failed.",
            "details": result.stderr or result.stdout,
        }), 500

    return send_file(OUTPUT_FILE, as_attachment=True, download_name="Final.xlsx")

if __name__ == "__main__":
    app.run()