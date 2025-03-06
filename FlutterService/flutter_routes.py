import logging
from PIL import Image
from bson import ObjectId
from bson.json_util import loads, dumps
from flask import Blueprint, request, jsonify
import io
from Grocery.Receipt import Receipt
from mongoClient.mongo_client import MongoConnector

from AzureDIConnection.DIConnection import analyze_receipt
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)
mongoClient = MongoConnector()

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
        collection = mongoClient.get_collection(db="receiptsdb", collection="receipts")
        
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

@flutter_bp.route('/search_generic', methods=['GET'])
def search_generic():
    try:
        collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")
            
        query = request.args.get("query")
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        agg_pipeline = [
            {
                "$search": {
                    "index": "default",
                    "autocomplete": {
                        "query": query,
                        "path": "genericItem",
                        "tokenOrder": "sequential",
                        "fuzzy": {
                            "maxEdits": 1,
                            "prefixLength": 2,
                            "maxExpansions": 256
                        }
                    }
                }
            },
            {"$limit": 20}
        ]

        results = list(collection.aggregate(agg_pipeline))

        for doc in results:
            doc["_id"] = str(doc["_id"])

            # If productIds become large, only send back _id and generalItem fields, then use the _id to query for productIds?
            if "productIds" in doc:
                doc["productIds"] = [str(id) for id in doc["productIds"]]

        print(results)
        return jsonify(results), 200
    except Exception as e:
        return f"An error occurred: {e}", 400
    
@flutter_bp.route('/get_storeProducts', methods=['POST'])
def get_storeProducts():
    try:
        collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 401
        if "productIds" not in data:
            return jsonify({"error": "productIds field is required"}), 401
        if data["productIds"] == []:
            return jsonify({"info": "No product of this type has been submitted"}), 200

        cur = collection.find({"_id": {'$in': [ObjectId(id) for id in data["productIds"]]}}, {'_id': 0, 'genericItemIds': 0}) # Excluding _id field from documents returned
        results = list(cur)

        return jsonify(results), 200
    except Exception as e:
        return f"An error occurred: {e}", 400