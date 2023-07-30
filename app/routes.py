from flask import request, jsonify
from app import app
from app.file_uploader import (
    PixeldrainHandler,
    BaidupanHandler,
    FileUploader
)

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
        uploader = FileUploader(file_path)
        try:
            uploader.upload_to_multiple([
                BaidupanHandler,
                PixeldrainHandler,
            ])
            return jsonify({"success": True,
                            "value": uploader.get_download_urls()})
        except Exception as e:
            print(e)
            return jsonify({"success": False, "message": "Server Error", "value": None}), 400
    else:
        return jsonify({"success": False, "message": "Invalid request", "value": None}), 400
