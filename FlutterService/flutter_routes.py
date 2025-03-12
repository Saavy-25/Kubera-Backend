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
                product.store_product_name = decoded_name
                                          
            logging.debug(f"Processed receipt: {receipt.get_map()}")
            return jsonify({'message': 'File successfully uploaded', 'receipt': receipt.get_map()}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500
    
# flutter app will call this endpoint to map product names to generic items after product names are verified by the user
@flutter_bp.route('/map_receipt', methods=['POST'])
def map_receipt():
    # TODO align with frontend request
    try:
        data = request.get_json()
        receipt = extract_receipt(data)
        # get product_name list
        product_names = [product.store_product_name for product in receipt.products]
        # get mapped name list
        generic_names = map_processor.processNames(product_names)

        collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")

        for name in generic_names:
            agg_pipeline = [
                                {
                                    "$search": {
                                        "text": {
                                            "query": name,
                                            "path": "genericName",
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
                                        "genericName": 1,
                                        "_id": 0,
                                        "score": {"$meta": "searchScore"},
                                    }
                                },
                                {"$sort": {"score": -1}}
                            ]
            
        query_results = list(collection.aggregate(agg_pipeline))

        # write results
        for i, name in enumerate(generic_names):
            top_generic_names = [result['genericName'] for result in query_results]
            if not top_generic_names or top_generic_names == []:
                receipt.products[i].generic_matches = [generic_names[i]]
            else:
                # in the case that there was no fuzzy match, just set to what was returned by name processor
                receipt.products[i].generic_matches = top_generic_names
                                          
        logging.debug(f"Processed receipt: {receipt.get_map()}")
        return jsonify({'message': 'File successfully uploaded', 'receipt': receipt.get_map()}), 200
       
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

# flutter app will call this endpoint to save receipt to mongo after user verifies data
@flutter_bp.route('/post_receipt', methods=['POST'])
def post_receipt():
    try:
        data = request.get_json()
        receipt = extract_receipt(data)
       
        # make sure that all store products (and associated generic items) exist in the storeProducts table before posting the full receipt
        post_store_products(receipt)
        
        # now add the receipt to the receipt db
        # Access the database and collection
        collection = mongoClient.get_collection(db="receiptdb", collection="receipts")
        result = collection.insert_one(receipt.get_mongo_entry())
    
        logging.debug(f"Data from mongo: {result}")
        
        return jsonify({"status": "success"}), 200
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
                                    "path": "genericName",
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
                                    "path": "genericName",
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
                    "genericName": 1,
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
    
@flutter_bp.route('/get_storeProducts/<generic_id>', methods=['GET'])
def get_storeProducts(generic_id):
    try:
        collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")
        cur = collection.find({"genericId": ObjectId(generic_id)}, {'_id': 0, 'genericId': 0}) # Excluding _id field from documents returned
        results = list(cur)

        return jsonify(results), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

# Currently not in use - just in case we want to refactor and only ping db for recentprices instead of the entire StoreProduct object
@flutter_bp.route('/get_recentPrices/<product_id>', methods=['GET'])
def get_productDetails(product_id):
    try:
        if not product_id:
            return jsonify({"error": "productId parameter is required"}), 400
        
        collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")
        result = collection.find_one({"_id": ObjectId(product_id)}, {'recentPrices': 1, "_id": 0})
        if not result:
            return jsonify({"error": "No product found with the given ID"}), 404

        return jsonify(result), 200
    except Exception as e:
        return f"An error occurred: {e}", 400
    
def extract_receipt(response_data):
    '''convert data from frontend request to receipt object'''
    required_fields = ['storeName', 'date', 'products', 'storeAddress', 'totalReceiptPrice']
        
    if not response_data:
        raise TypeError("Invalid input, function requires JSON data field")
    for field in required_fields:
        if field not in response_data or response_data.get(field) == "" or response_data.get(field) is None:
            raise ValueError("Required fields missing or empty")
            
    # Extract receipt details from JSON
    store_name = response_data.get('storeName')
    date = response_data.get('date')
    products = response_data.get('products')
    store_address = response_data.get('storeAddress')
    total_receipt_price = response_data.get('totalReceiptPrice')
    
    # Convert JSON product data into StoreProduct objects
    # products = [StoreProduct(**product) for product in products]
    product_objects = []
    for product in products:
        product_objects.append(StoreProduct(line_item=product["lineItem"], count=product["count"], total_price=product["totalPrice"], store_name=product["storeName"], store_product_name=product["storeProductName"], generic_matches=product["genericMatches"]))
    
    # Create a Receipt instance
    receipt = Receipt(store_name=store_name, date=date, products=product_objects, store_address=store_address, total_receipt_price=total_receipt_price)
    return receipt

def post_generic_items(receipt):
    '''find/create the generic id for the given product'''
    # if the generic item is in the db, add the id to the product object
    # if the generic items is not in the db, add the generic item to the db and add the id to the product object
    collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")

    for product in receipt.products:

        doccument = collection.find_one({"genericName": product.generic_matches[0]})

        if doccument:
            product.generic_id = doccument["_id"]
        else:
            product.generic_id = collection.insert_one({"genericName": product.generic_matches[0]}).inserted_id

def post_store_products(receipt):
    '''find/create the product id for the given product'''

    # should call post generic items first, to make sure that each posted product has a generic id
    post_generic_items(receipt)

    # if the store product is in the db, add the id to the product object, update the recent prices
    # if the store product is not in the db, add the store product to the db and then add the id to the product object
    collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")

    for product in receipt.products:

        product.store_name = receipt.store_name
        product.date = receipt.date

        if not (product.store_product_name and product.store_name and product.generic_id and product.price_per_count and product.date):
            ValueError("Valid store product required to create a store product")

        query = {"storeProductName": product.store_product_name, "storeName": receipt.store_name}

        doccument = collection.find_one(query)

        if doccument:
            # if the store product is in the db, add the id to the product object, update the recent prices
            # store the id
            product.id = doccument["_id"]
            prices = doccument["recentPrices"]
            prices.append([product.price_per_count, receipt.date])
            prices = prices[-5:]
            update_operation = { '$set' : {'recentPrices' : prices}}
            collection.update_one(query, update_operation)
        else:
            # insert the product, set the id
            product.id = collection.insert_one(product.first_mongo_entry()).inserted_id