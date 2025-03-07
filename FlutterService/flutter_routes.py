import logging
from PIL import Image
from flask import Blueprint, request, jsonify
import io
from Grocery.Receipt import Receipt
from Grocery.StoreProduct import StoreProduct
from mongoClient.mongo_client import mongoClient
from NameProcessing.NameProcessor import NameProcessor

from AzureDIConnection.DIConnection import analyze_receipt
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)
decode_processor = NameProcessor(prompt_path="./NameProcessing/.decode_prompt")
map_processor = NameProcessor(prompt_path="./NameProcessing/.map_prompt")

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
            logging.debug(f"io: {img_io}")
            img.save(img_io, 'JPEG')
            receipt = analyze_receipt(img_io)

            # get line_item list
            line_items = [product.line_item for product in receipt.products]
            # get decoded name list
            product_names = decode_processor.processNames(line_items)
            # write results
            for product, decoded_name in zip(receipt.products, product_names):
                product.product_name = decoded_name
                                          
            logging.debug(f"Processed receipt: {Receipt.getMap(receipt)}")
            return jsonify({'message': 'File successfully uploaded', 'receipt': Receipt.getMap(receipt)}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500
    
# flutter app will call this endpoint to map product names to generic items after product names are verified by the user
@flutter_bp.route('/map_receipt', methods=['POST'])
def map_receipt():
    # TODO align with frontend request
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid input, JSON required'}), 500
        
        # Extract receipt details from JSON
        store_name = data.get('store_name', "")
        date = data.get('date', "")
        product_list = data.get('products', [])
        
        # Convert JSON product data into StoreProduct objects
        products = [StoreProduct(**product) for product in product_list]
        
        # Create a Receipt instance
        receipt = Receipt(store_name=store_name, date=date, products=products)
        # get product_name list
        product_names = [product.product_name for product in receipt.products]
        # get mapped name list
        generic_names = map_processor.processNames(product_names)
        # write results
        for product, mapped_name in zip(receipt.products, generic_names):
            product.generic_name = mapped_name
                                          
        logging.debug(f"Processed receipt: {Receipt.getMap(receipt)}")
        return jsonify({'message': 'File successfully uploaded', 'receipt': Receipt.getMap(receipt)}), 200
       
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

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