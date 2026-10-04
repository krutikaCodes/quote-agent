from pathlib import Path
import subprocess
import sys
import base64

from flask import Flask, request, jsonify

app = Flask(__name__)

APP_DIR = Path(__file__).resolve().parent
INPUT_DIR = APP_DIR / "Input"
OUTPUT_FILE = APP_DIR / "Output" / "Final.xlsx"


@app.route("/", methods=["GET"])
def index():
    return "Quote Agent API Running"


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()

        services_content = data["services"]
        standard_content = data["standard"]

        INPUT_DIR.mkdir(exist_ok=True)
        OUTPUT_FILE.parent.mkdir(exist_ok=True)

        services_path = INPUT_DIR / "Services.pdf"
        standard_path = INPUT_DIR / "Standard.xlsx"

        # Decode incoming Base64 files
        with open(services_path, "wb") as f:
            f.write(base64.b64decode(services_content))

        with open(standard_path, "wb") as f:
            f.write(base64.b64decode(standard_content))

        # Run your existing script
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
        )

        if result.returncode != 0:
            return jsonify({
                "error": "Generation failed",
                "details": result.stderr or result.stdout
            }), 500

        # Convert generated file back to Base64
        with open(OUTPUT_FILE, "rb") as f:
            file_b64 = base64.b64encode(f.read()).decode()

        return jsonify({
            "file": file_b64
        })

    except Exception as e:
        return jsonify({
   
