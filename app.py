# from pathlib import Path
# import subprocess
# import sys
# import base64

# from flask import Flask, request, jsonify

# app = Flask(__name__)

# APP_DIR = Path(__file__).resolve().parent
# INPUT_DIR = APP_DIR / "Input"
# OUTPUT_DIR = APP_DIR / "Output"
# OUTPUT_FILE = OUTPUT_DIR / "Final.xlsx"


# @app.route("/", methods=["GET"])
# def home():
#     return "Quote Agent API Running"


# @app.route("/generate", methods=["POST"])
# def generate():
#     try:
#         data = request.get_json()

#         if not data:
#             return jsonify({
#                 "error": "No JSON payload received."
#             }), 400

#         services_content = data.get("services")
#         standard_content = data.get("standard")

#         if not services_content or not standard_content:
#             return jsonify({
#                 "error": "Both services and standard files are required."
#             }), 400

#         INPUT_DIR.mkdir(exist_ok=True)
#         OUTPUT_DIR.mkdir(exist_ok=True)

#         services_path = INPUT_DIR / "Services.pdf"
#         standard_path = INPUT_DIR / "Standard.xlsx"

#         # Save PDF
#         with open(services_path, "wb") as f:
#             f.write(base64.b64decode(services_content))

#         # Save Excel
#         with open(standard_path, "wb") as f:
#             f.write(base64.b64decode(standard_content))

#         # Run Python script
#         result = subprocess.run(
#             [
#                 sys.executable,
#                 str(APP_DIR / "generate_final.py"),
#                 str(services_path),
#                 str(standard_path),
#                 str(OUTPUT_FILE)
#             ],
#             capture_output=True,
#             text=True,
#             cwd=APP_DIR
#         )

#         if result.returncode != 0:
#             return jsonify({
#                 "error": "generate_final.py failed",
#                 "stdout": result.stdout,
#                 "stderr": result.stderr
#             }), 500

#         if not OUTPUT_FILE.exists():
#             return jsonify({
#                 "error": "Final.xlsx was not created."
#             }), 500

#         # Convert output file to Base64
#         with open(OUTPUT_FILE, "rb") as f:
#             output_b64 = base64.b64encode(f.read()).decode()

#         return jsonify({
#             "status": "success",
#             "file": output_b64
#         })

#     except Exception as e:
#         return jsonify({
#             "error": str(e)
#         }), 500


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

from pathlib import Path
import subprocess
import sys
import base64

from flask import Flask, request, jsonify

app = Flask(__name__)

APP_DIR = Path(__file__).resolve().parent

INPUT_DIR = APP_DIR / "Input"
OUTPUT_DIR = APP_DIR / "Output"

SERVICES_FILE = INPUT_DIR / "Services.pdf"
STANDARD_FILE = INPUT_DIR / "Standard.xlsx"
OUTPUT_FILE = OUTPUT_DIR / "Final.xlsx"


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.get_json()

        services_content = data.get("services")
        standard_content = data.get("standard")

        if not services_content or not standard_content:
            return jsonify({
                "error": "Missing services or standard file"
            }), 400

        INPUT_DIR.mkdir(exist_ok=True)
        OUTPUT_DIR.mkdir(exist_ok=True)

        # Save PDF
        if str(services_content).startswith("%PDF"):
            pdf_bytes = services_content.encode("latin1")
        else:
            pdf_bytes = base64.b64decode(services_content)
        
        with open(SERVICES_FILE, "wb") as f:
            f.write(pdf_bytes)
        
        # Save Excel
        if str(standard_content).startswith("PK"):
            excel_bytes = standard_content.encode("latin1")
        else:
            excel_bytes = base64.b64decode(standard_content)
        
        with open(STANDARD_FILE, "wb") as f:
            f.write(excel_bytes)

        # Run generate_final.py
        result = subprocess.run(
            [
                sys.executable,
                "generate_final.py",
                str(SERVICES_FILE),
                str(STANDARD_FILE),
                str(OUTPUT_FILE)
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "error": result.stderr,
                "stdout": result.stdout
            }), 500

        if not OUTPUT_FILE.exists():
            return jsonify({
                "error": "Final.xlsx was not created"
            }), 500

        return jsonify({
            "message": "output_created",
            "output_size": OUTPUT_FILE.stat().st_size
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/", methods=["GET"])
def home():
    return "Quote Agent API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

