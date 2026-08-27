from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
# This is the magic line that allows React to talk to Python
CORS(app, resources={r"/*": {"origins": "*"}}) 

DATA_FILE = 'progress.json'

@app.route('/get-questions', methods=['GET'])
def get_questions():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return jsonify(json.load(f))
    return jsonify([])

@app.route('/update-status', methods=['POST'])
def update_status():
    data = request.json
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # Changed port to 5001
    app.run(host='127.0.0.1', port=5001, debug=True)