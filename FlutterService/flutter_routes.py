import logging
from PIL import Image
from flask import Blueprint, request, jsonify
import io

from AzureDIConnection.DIConnection import analyze_receipts
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)

logging.basicConfig(level=logging.DEBUG)

# flutter app will call this endpoint to send image data
@flutter_bp.route('/process_receipt', methods=['POST'])
def process_receipt():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file:
            # Process the file here
            logging.debug(f"Received file: {file.filename}")
            # change format of the file
            img = Image.open(file.stream)
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG')
            receipt = analyze_receipts(img_io)
            logging.debug(f"Processed receipt: {receipt}")
            return jsonify({'message': 'File successfully uploaded'}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500

# flutter app will call this endpoint to save receipt to mongo after user verifies data
# @flutter_bp.route('/save_receipt', methods=['POST'])
# def send_data():
#     data = request.get_json()
#     # Process the received data here

#     # call mongo client and post data to mongo
#     try:
#         add_receipt_data(data) # posts to mongo
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500

#     return jsonify({"status": "success", "data_received": data}), 200


@flutter_bp.route('/get_data', methods=['GET'])
def receive_data():
    # Prepare the data to be sent to the Flutter app
    data = {"message": "Hello from the server!"}
    return jsonify(data), 200