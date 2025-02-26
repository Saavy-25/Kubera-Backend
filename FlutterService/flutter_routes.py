import logging
from PIL import Image
from flask import Blueprint, request, jsonify
import io
from Grocery.Receipt import Receipt
from mongoClient.mongo_client import mongoClient

from AzureDIConnection.DIConnection import analyze_receipt
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
            receipt = analyze_receipt(img_io)

            # TODO: send receipt to mapping pipleine to generalize line items and populate generic matches array

            for product in receipt.products:
                # can use product.line_item to get product name
                # product.product_name = 
                # product.generic_matches = 
            
            logging.debug(f"Processed receipt: {Receipt.getMap(receipt)}")
            return jsonify({'message': 'File successfully uploaded', 'receipt': Receipt.getMap(receipt)}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500

# flutter app will call this endpoint to save receipt to mongo after user verifies data
@flutter_bp.route('/post_receipt', methods=['POST'])
def post_receipt():
    try:
        data = request.get_json()
        # Process the received data here
        # TODO: clean up possible generic matches array and only keep match selected from user
        logging.debug(f"Data from client: {data}")
        
        # Access the database and collection
        db = mongoClient["receiptdb"]
        collection = db["receipts"]
        
        # Insert the data into the collection
        result = collection.insert_one(data)
        logging.debug(f"Data from mongo: {result}")
        
        return jsonify({"status": "success", "data_received": data}), 200
    except Exception as e:
        logging.error(f"Error posting receipt to MongoDB: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@flutter_bp.route('/get_data', methods=['GET'])
def receive_data():
    # Prepare the data to be sent to the Flutter app
    data = {"message": "Hello from the server!"}
    return jsonify(data), 200