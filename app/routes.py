from flask import request, jsonify
import threading

from app import app
from app.file_uploader import upload

@app.route('/', methods=['GET'])
def greet():
    """
    Greet the user with a JSON response.
    """
    return jsonify({'message': 'Hello!'})

@app.errorhandler(404)
def page_not_found(e):
    """
    Handle 404 errors and return a JSON response.
    """
    return jsonify({'error': 'Page not found'}), 404

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    file_path = request.json.get('file_path')
    if file_path:
        threading.Thread(target=upload, args=(file_path,)).start()
        return jsonify({"success": True, "message": "File added to upload"})
    else:
        return jsonify({"success": False, "message": "Invalid request", "value": None}), 400
