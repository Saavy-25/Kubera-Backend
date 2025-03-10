import logging
from PIL import Image
from bson import ObjectId
from bson.json_util import loads, dumps
from flask import Blueprint, request, jsonify
import io
from Grocery.Receipt import Receipt
from Grocery.StoreProduct import StoreProduct
from NameProcessing.NameProcessor import NameProcessor
from mongoClient.mongo_client import MongoConnector


from AzureDIConnection.DIConnection import analyze_receipt
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)

decode_processor = NameProcessor(prompt_path="./NameProcessing/.decode_prompt")
map_processor = NameProcessor(prompt_path="./NameProcessing/.map_prompt")

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
                                          
            logging.debug(f"Processed receipt: {Receipt.get_map(receipt)}")
            return jsonify({'message': 'File successfully uploaded', 'receipt': Receipt.get_map(receipt)}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500
    
# flutter app will call this endpoint to map product names to generic items after product names are verified by the user
@flutter_bp.route('/map_receipt', methods=['POST'])
def map_receipt():
    # TODO align with frontend request
    try:
        data = request.get_json()
        required_fields = ['store_name', 'date', 'products', 'store_address', 'total_receipt_price']

        if not data:
            return jsonify({'error': 'Invalid input, JSON required'}), 500
        if required_fields not in data:
            return jsonify({'error': 'Missing required receipt fields'}), 500
        for field in required_fields:
            if data.get(field) == "" or data.get(field) is None:
                return jsonify({'error': 'Required fields cannot be empty'}), 500
        
        # Extract receipt details from JSON
        store_name = data.get('store_name')
        date = data.get('date')
        products = data.get('products')
        store_address = data.get('store_address')
        total_receipt_price = data.get('total_receipt_price')
        
        # Convert JSON product data into StoreProduct objects
        products = [StoreProduct(**product) for product in products]
        
        # Create a Receipt instance
        receipt = Receipt(store_name=store_name, date=date, products=products, store_address=store_address, total_receipt_price=total_receipt_price)
        # get product_name list
        product_names = [product.product_name for product in receipt.products]
        # get mapped name list
        generic_names = map_processor.processNames(product_names)

        collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")

        for name in generic_names:
            agg_pipeline = [
                                {
                                    "$search": {
                                        "text": {
                                            "query": name,
                                            "path": "genericItem",
                                            "fuzzy": {
                                                "maxEdits": 1,
                                                "maxExpansions": 100
                                            }
                                        }
                                    }
                                },
                                {"$limit": 3}, # top 3 matches
                                {
                                    "$project": {
                                        "genericItem": 1,
                                        "_id": 0,
                                        "score": {"$meta": "searchScore"},
                                    }
                                },
                                {"$sort": {"score": -1}}
                            ]
            
        query_results = list(collection.aggregate(agg_pipeline))

        # write results
        for i, name in enumerate(generic_names):
            top_generic_names = [result['genericItem'] for result in query_results]
            receipt.products[i].generic_name = top_generic_names
                                          
        logging.debug(f"Processed receipt: {Receipt.get_map(receipt)}")
        return jsonify({'message': 'File successfully uploaded', 'receipt': Receipt.get_map(receipt)}), 200
       
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
                    "compound": {
                        "should": [
                            {
                                "autocomplete": {
                                    "query": query,
                                    "path": "genericItem",
                                    "tokenOrder": "any",
                                    "fuzzy": {
                                        "maxEdits": 1,
                                        "maxExpansions": 100
                                    },
                                }
                            },
                            {
                                "text": {
                                    "query": query,
                                    "path": "genericItem",
                                    "fuzzy": {
                                        "maxEdits": 1,
                                        "maxExpansions": 100
                                    }
                                }
                            }
                        ],
                        "minimumShouldMatch": 1
                    }
                }
            },
            {
                "$limit": 10
            },
            {
                "$project":
                {
                    "genericItem": 1,
                    "_id": 1,
                    "score": {"$meta": "searchScore"},
                }
            },
            {
                "$sort": {
                    "score": -1
                }
            }
        ]

        results = list(collection.aggregate(agg_pipeline))
        print(results)

        for doc in results:
            doc["_id"] = str(doc["_id"])

            # If productIds become large, only send back _id and generalItem fields, then use the _id to query for productIds?
            if "productIds" in doc:
                doc["productIds"] = [str(id) for id in doc["productIds"]]

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
            return jsonify({"error": "No productId provided"}), 401

        cur = collection.find({"_id": {'$in': [ObjectId(id) for id in data["productIds"]]}}, {'_id': 0, 'genericItemIds': 0}) # Excluding _id field from documents returned
        results = list(cur)

        return jsonify(results), 200
    except Exception as e:
        return f"An error occurred: {e}", 400