from flask import Flask, request, jsonify
from flask_cors import CORS
from middleware import fetch_repo_and_analyze, analyze_uploaded_file

app = Flask(__name__)
CORS(app)

@app.route("/upload/", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    content = file.read()

    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "File must be UTF-8 text"}), 400

    result = analyze_uploaded_file(text)
    print(result)
    return jsonify(result)


@app.route("/analyze_repo/", methods=["POST"])
def analyze_repo():
    data = request.get_json()

    if not data or "github_url" not in data:
        return jsonify({"error": "github_url is required"}), 400

    result = fetch_repo_and_analyze(data["github_url"])
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=False)
