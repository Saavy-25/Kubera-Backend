from collections import defaultdict, deque
import logging
from PIL import Image
from bson import ObjectId
from bson.json_util import loads, dumps
from flask import Blueprint, request, jsonify, Response
import io
from Dashboard.Dashboard import Dashboard
from Dashboard.DashboardManager import DashboardManager
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from
from Users.User import User
from Grocery.ScannedReceipt import ScannedReceipt
from Grocery.ScannedLineItem import ScannedLineItem
from NameProcessing.NameProcessor import NameProcessor
from NameProcessing.EmbeddingVectorManager import EmbeddingVectorManager
from mongoClient.mongo_client import MongoConnector
from flask_login import current_user
from FlutterService.ClientErrorMessage import ClientErrorMessage
from datetime import datetime, timezone

from AzureDIConnection.DIConnection import analyze_receipt
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)

decode_processor = NameProcessor(prompt_key="DECODE_PROMPT", cache_path="NameProcessing/.decode_cache.json")
map_processor = NameProcessor(prompt_key="MAP_PROMPT", cache_path="NameProcessing/.map_cache.json")
embedding_vector_manager = EmbeddingVectorManager(cache_path="NameProcessing/.vector_cache.json")

mongoClient = MongoConnector()

logging.basicConfig(level=logging.DEBUG)

datetime_format = '%Y-%m-%d' # yyyy-mm-dd format

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
            scanned_receipt = analyze_receipt(img_io)

            # get line_item list
            line_item_abrev = [scanned_line_item.line_item for scanned_line_item in scanned_receipt.scanned_line_items]

            # get decoded name list
            product_names = decode_processor.processNames(line_item_abrev)
            # write results
            for product, decoded_name in zip(scanned_receipt.scanned_line_items, product_names):
                product.store_product_name = decoded_name
                                          
            logging.debug(f"Processed receipt: {scanned_receipt.flutter_response()}")
            return jsonify({'message': 'File successfully uploaded', 'receipt': scanned_receipt.flutter_response()}), 200
    except Exception as e:
        logging.error(f"Error processing receipt: {e}")
        return jsonify({'error': 'An error occurred while processing the receipt'}), 500
    
# flutter app will call this endpoint to map product names to generic items after product names are verified by the user
@flutter_bp.route('/map_receipt', methods=['POST'])
def map_receipt():
    try:
        data = request.get_json()
        scanned_receipt = extract_receipt(data)
        # get product_name list
        product_names = [scanned_line_item.store_product_name for scanned_line_item in scanned_receipt.scanned_line_items]
        # get mapped name list
        generic_names = map_processor.processNames(product_names)

        collection = mongoClient.get_collection(collection="genericItems")

        # confirm all generic items in the database have an embedding
        # if no embedding, one is generated and added to the database
        for doc in collection.find({"vectorEmbedding": ""}):
            name = doc["genericName"]
            embedding = embedding_vector_manager.getEmbedding(name)
            collection.update_one(
                {"_id": doc["_id"]},
                {"$set": {"vectorEmbedding": embedding}}
            )

        # go through each generic item from api call
        for i, name in enumerate(generic_names):
            embedding = embedding_vector_manager.getEmbedding(name)
            agg_pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "vectorEmbedding",
                        "queryVector": embedding,
                        "numCandidates": 1000,
                        "limit": 3
                    }
                },
                {
                    "$project": {
                        "genericName": 1,
                        "_id": 0,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
            ]

            # find existing genericItems in db that are the closest match, and collect their genericNames
            query_results = list(collection.aggregate(agg_pipeline))

            # filter out the results if their matching score is less than 0.95
            top_generic_names = [result['genericName'] for result in query_results if result['score'] > 0.95]
            print(f'Before add: {top_generic_names}')

            # in the case that no match is found or it is more accurate, include the name generated by the api as an option
            if name not in top_generic_names:
                top_generic_names.insert(0, name)
            print(f'After add: {top_generic_names}')

            scanned_receipt.scanned_line_items[i].generic_matches = top_generic_names
                                          
        logging.debug(f"Processed receipt: {scanned_receipt.flutter_response()}")
        return jsonify({'message': 'File successfully uploaded', 'receipt': scanned_receipt.flutter_response()}), 200
       
    except ValueError as e:
        logging.error(f"Missing information from receipt")
        e = ClientErrorMessage(message="Please fill in missing receipt fields.", detail="Required receipt field missing or blank")
        return jsonify(e.flutter_response()), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

# flutter app will call this endpoint to save receipt to mongo after user verifies data
@flutter_bp.route('/post_receipt', methods=['POST'])
def post_receipt():
    try:
        if request.cookies and request.cookies['session'] and not current_user.is_authenticated:
            logging.error(f"Frontend login session not in sync with server")
            e = ClientErrorMessage(message="Our servers lost your login session, please log in again and rescan receipt.", detail="Frontend login session not in sync with server")
            return jsonify(e.flutter_response()), 401

        data = request.get_json()
        scanned_receipt = extract_receipt(data)
       
        # make sure that all store products (and associated generic items) exist in the storeProducts table before posting the full receipt
        post_store_products(scanned_receipt)

        # update total receipt price
        total_receipt_price = 0
        for scanned_line_item in scanned_receipt.scanned_line_items:
            total_receipt_price += scanned_line_item.price_per_count
        
        scanned_receipt.total_receipt_price = total_receipt_price
        
        # now add the receipt to the receipt db
        # Access the database and collection
        collection = mongoClient.get_collection(collection="receipts")
        receipt_id = str(collection.insert_one(scanned_receipt.get_mongo_entry()).inserted_id)
        
        if current_user.is_authenticated:
            # Add the receipt ID to the user's receipt IDs
            logging.debug(f"User authenticated")
            user_collection = mongoClient.get_collection(collection="users")
            query = {"username": current_user.username}
            current_user.receipt_ids.append(receipt_id)
            update_operation = { '$set' : {'receiptIds' : current_user.receipt_ids}}
            user_collection.update_one(query, update_operation)
            
    
        logging.debug(f"Data from mongo: {receipt_id}")
        
        # update data for dashboard analytics if user is logged in
        if current_user.is_authenticated:
            # get dashboard data from database with user_id
            collection = mongoClient.get_collection(collection="dashboards")
            dashboard_data = collection.find_one({"username": current_user.username}, {'_id': 0})

            # create Dashboard object
            if dashboard_data:
                dashboard = Dashboard(**dashboard_data)
            else:
                dashboard = Dashboard(current_user.username)  # create an empty Dashboard if none exists

            # update dashboard data
            dashboard_manager = DashboardManager()
            dashboard_manager.update_dashboard(dashboard, scanned_receipt)

            # update dashboard in the database
            collection.update_one(
                {"username": dashboard.username},
                {"$set": dashboard.get_mongo_entry()},
                upsert=True
            )
            
            logging.debug("Dashboard updated successfully.")


        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"Error posting receipt to MongoDB: {e}")
        e = ClientErrorMessage(message="We are having trouble saving your recipt, please try again.", detail=str(e))
        return jsonify(e.flutter_response()), 500


@flutter_bp.route('/get_data', methods=['GET'])
def receive_data():
    # Prepare the data to be sent to the Flutter app
    data = {"message": "Hello from the server!"}
    return jsonify(data), 200

@flutter_bp.route('/search_generic', methods=['GET'])
def search_generic():
    try:
        collection = mongoClient.get_collection(collection="genericItems")
            
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
                                        "maxExpansions": 20
                                    },
                                }
                            },
                            {
                                "text": {
                                    "query": query,
                                    "path": "genericName",
                                    "fuzzy": {
                                        "maxEdits": 1,
                                        "maxExpansions": 20
                                    }
                                }
                            }
                        ],
                        "minimumShouldMatch": 1
                    },
                    "highlight": {
                        "path": "genericName"
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
                    "highlights": { "$meta": "searchHighlights" }
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
        collection = mongoClient.get_collection(collection="storeProducts")
        cur = collection.find({"genericId": ObjectId(generic_id)}, {'_id': 1, 'genericId': 0}) # Excluding _id field from documents returned
        results = [
            {**item, "id": str(item.pop("_id"))} for item in cur
        ] # cast id to string and remove underscore from key
        for item in results: # remove all the objectIds
            item.pop("_id", None)

        print(f"db query: {results}")
        return jsonify(results), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

# Currently not in use - just in case we want to refactor and only ping db for recentprices instead of the entire StoreProduct object
@flutter_bp.route('/get_recentPrices/<product_id>', methods=['GET'])
def get_productDetails(product_id):
    try:
        if not product_id:
            return jsonify({"error": "productId parameter is required"}), 400
        
        collection = mongoClient.get_collection(collection="storeProducts")
        result = collection.find_one({"_id": ObjectId(product_id)}, {'recentPrices': 1, "_id": 0})
        if not result:
            return jsonify({"error": "No product found with the given ID"}), 404

        return jsonify(result), 200
    except Exception as e:
        return f"An error occurred: {e}", 400
    
def extract_receipt(response_data):
    '''convert data from frontend request to receipt object'''
    required_fields = ['storeName', 'date', 'scannedLineItems', 'storeAddress', 'totalReceiptPrice']
        
    if not response_data:
        raise TypeError("Invalid input, function requires JSON data field")
    for field in required_fields:
        if field not in response_data or response_data.get(field) == "" or response_data.get(field) is None:
            raise ValueError("Required fields missing or empty")
            
    # Extract receipt details from JSON
    store_name = response_data.get('storeName')
    date = response_data.get('date')
    scanned_line_items = response_data.get('scannedLineItems')
    store_address = response_data.get('storeAddress')
    total_receipt_price = response_data.get('totalReceiptPrice')
    
    # Convert JSON product data into StoreProduct objects
    # products = [StoreProduct(**product) for product in products]
    line_item_objects = []
    for scanned_line_item in scanned_line_items:
        line_item_objects.append(ScannedLineItem(line_item=scanned_line_item["lineItem"], count=scanned_line_item["count"], total_price=scanned_line_item["totalPrice"], store_product_name=scanned_line_item["storeProductName"], generic_matches=scanned_line_item["genericMatches"]))
    
    # Create a Receipt instance
    scanned_receipt = ScannedReceipt(store_name=store_name, date=date, scanned_line_items=line_item_objects, store_address=store_address, total_receipt_price=total_receipt_price)
    return scanned_receipt

def post_generic_items(scanned_receipt):
    '''find/create the generic id for the given product'''
    # if the generic item is in the db, add the id to the product object
    # if the generic items is not in the db, add the generic item to the db and add the id to the product object
    collection = mongoClient.get_collection(collection="genericItems")

    for scanned_line_item in scanned_receipt.scanned_line_items:
        generic_name = scanned_line_item.generic_matches[0]
        document = collection.find_one({"genericName": generic_name})

        if document:
            scanned_line_item.generic_id = document["_id"]
        else:
            vector_embedding = embedding_vector_manager.getEmbedding(generic_name)
            new_document = {
                "genericName": generic_name,
                "vectorEmbedding": vector_embedding
            }
            scanned_line_item.generic_id = collection.insert_one(new_document).inserted_id

def post_store_products(scanned_receipt):
    '''find/create the product id for the given product'''

    # should call post generic items first, to make sure that each posted product has a generic id
    try:
        post_generic_items(scanned_receipt)

    # if the store product is in the db, add the id to the product object, update the recent prices
    # if the store product is not in the db, add the store product to the db and then add the id to the product object
        collection = mongoClient.get_collection(collection="storeProducts")

        for scanned_line_item in scanned_receipt.scanned_line_items:

            scanned_line_item.store_name = scanned_receipt.store_name
            scanned_line_item.date = scanned_receipt.date

            if not (scanned_line_item.store_product_name and scanned_line_item.store_name and scanned_line_item.generic_id and scanned_line_item.price_per_count and scanned_line_item.date):
                ValueError("Valid store product required to create a store product")

            query = {"storeProductName": scanned_line_item.store_product_name, "storeName": scanned_receipt.store_name}

            document = collection.find_one(query)

            if document:
                # if the store product is in the db, add the id to the product object, update the recent prices
                # store the id
                scanned_line_item.id = document["_id"]

                curr_price = scanned_line_item.price_per_count
                curr_date = scanned_line_item.date
                recent_prices = update_recent_prices(curr_price, curr_date, document['recentPrices'])

                update_operation = { '$set' : {'recentPrices' : recent_prices}}
                collection.update_one(query, update_operation)
            else:
                # insert the product, set the id
                scanned_line_item.id = collection.insert_one(scanned_line_item.first_mongo_entry()).inserted_id
    except Exception as e:
        logging.debug('An error has occurred: ', e)
    except ValueError as ve:
        logging.debug(ve)

def update_recent_prices(curr_price, curr_date, recent_prices):
    new_report = {
                'price': curr_price,
                'reportCount': 1,
                'lastReportDate': curr_date
            }
            
    _recent, idx = insert_report(recent_prices, new_report)
    if idx < len(recent_prices):
        for p in recent_prices[idx:]:
            _recent.append(p)

    # _recent = squash_reports(_recent)
    
    return _recent[:10]

def insert_report(recent_prices, new_report):
    _recent = []
    curr_date = datetime.strptime(new_report['lastReportDate'], datetime_format)
    curr_price = new_report['price']

    idx = 0
    while idx < len(recent_prices):
        report = recent_prices[idx]
        last_date = datetime.strptime(report['lastReportDate'], datetime_format)
        
        if curr_date > last_date:
            if curr_price != report['price']:
                # New price reported latest
                _recent.append(new_report)
                return _recent, idx
            
            # Same price reported latest
            report['lastReportDate'] = new_report['lastReportDate']
            report['reportCount'] += 1
            _recent.append(report)
            idx += 1
            return _recent, idx
        
        # Price reported on a recorded date
        if curr_date == last_date:
            same_date_prices = []

            i = idx
            inserted = False
            # Look through all prices reported on the same date
            while i < len(recent_prices) and recent_prices[i]['lastReportDate'] == new_report['lastReportDate']:
                if recent_prices[i]['price'] == curr_price:
                    recent_prices[i]['reportCount'] += 1
                    same_date_prices.append(recent_prices[i])
                    inserted = True
                else:
                    same_date_prices.append(recent_prices[i])
                i += 1
            
            if not inserted:
                same_date_prices.append(new_report)
            
            same_date_prices.sort(key=lambda x: x['reportCount'], reverse=True)

            for price in same_date_prices:
                _recent.append(price)
            
            idx = i # idx tells the upper level method where to start slicing and appending the rest of the recent prices array
            return _recent, idx

        _recent.append(report)
        idx += 1      
    
    _recent.append(new_report)
    return _recent, idx

## WIP, not necessary for final deliverable, more like wishful thinking that we'd have this mechanism
# def squash_reports(recent):
#     # Group reports by lastReportDate
#     grouped_reports = defaultdict(list)
#     for report in recent:
#         grouped_reports[report['lastReportDate']].append(report)

#     squashed = []
#     for date, reports in grouped_reports.items():
#         if len(reports) == 1:
#             squashed.append(reports[0])
#             continue

#         # Sort reports by reportCount in descending order
#         reports.sort(key=lambda x: x['reportCount'], reverse=True)

#         # Check if the change between the highest and second highest reportCount is >= 50%
#         if len(reports) > 1 and (reports[0]['reportCount'] - reports[1]['reportCount']) / reports[1]['reportCount'] >= 0.5:
#             squashed.append(reports[0])
#             continue
#         else:
#             squashed.extend(reports)

#     return squashed

@flutter_bp.route('/get_dashboard_data', methods=["GET"])
@login_required
def get_dashboard_data():
    try:
        collection = mongoClient.get_collection(collection="dashboards")
        user_dashboard_data = collection.find_one({"username": current_user.username}, {'_id': 0}) # each user has one dashboard
        if user_dashboard_data:
            dashboard = Dashboard(**user_dashboard_data)
            return jsonify(dashboard.flutter_response()), 200
        else:
            # user has not uploaded any receipts yet
            return jsonify({"message": "No dashboard data available yet."}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/get_user_lists', methods=["GET"])
def get_user_lists():
    try:
        username = current_user.username
        if not username:
            return jsonify({"error": "Missing user cookie"}), 400

        users_collection = mongoClient.get_collection(collection="users")
        user_list_ids = users_collection.find_one({"username": username},  {"shoppingListIds": 1})
        shoppingLists_collection = mongoClient.get_collection(collection="shoppingLists")

        if not user_list_ids or "shoppingListIds" not in user_list_ids:
            return jsonify({"message": "No user with this id could be found."}), 200

        shopping_list_ids = [ObjectId(id) for id in user_list_ids["shoppingListIds"]]

        shopping_lists = shoppingLists_collection.find(
            {"_id": {"$in": shopping_list_ids}}
        )

        shopping_lists_data = [
            {
            "id": str(item["_id"]),
            "listName": item.get("listName", ""),
            "items": item.get("items", []),
            "date": item.get("date", "").strftime('%Y-%m-%d') if item.get("date") else ""
            }
            for item in shopping_lists
        ]

        return jsonify(shopping_lists_data), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/get_list_data/<list_id>', methods=["GET"])
def get_list_data(list_id):
    try:      
        shopping_list_collection = mongoClient.get_collection(collection="shoppingLists")

        shopping_list = shopping_list_collection.find_one(
            {"_id": ObjectId(list_id)}
        )
        if shopping_list and "date" in shopping_list and isinstance(shopping_list["date"], datetime):
            shopping_list["date"] = shopping_list["date"].strftime('%Y-%m-%d')

        if not shopping_list:
            return jsonify({"message": "Shopping list not found"}), 404

        shopping_list["id"] = str(shopping_list["_id"])
        return Response(dumps(shopping_list), mimetype='application/json'), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/add_item_to_list', methods=["PUT"])
def add_item_to_list():
    try:      
        data = request.get_json()
        list_id = data.get('listId')
        store_product_id = data.get('storeProductId')
        product_name = data.get('productName')

        # Required fields check
        if not list_id or not store_product_id or not product_name:
            return jsonify({"error": "Missing required fields"}), 400

        shopping_list_collection = mongoClient.get_collection(collection="shoppingLists")

        new_item = {
            "productName": product_name,
            "storeProductId": store_product_id,
            "retrieved": False
        }

        result = shopping_list_collection.update_one(
            {"_id": ObjectId(list_id)},
            {"$push": {"items": new_item}}
        )

        if result.matched_count == 0:
            return jsonify({"error": "Shopping list not found"}), 404

        return jsonify({"message": "Item added successfully"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/toggle_list_item', methods=["PUT"])
def toggle_list_item():
    try:      
        data = request.get_json()
        list_id = data.get("listId")
        store_product_id = data.get("storeProductId")

        if not list_id or not store_product_id:
            return jsonify({"error": "listId and storeProductId are required"}), 400

        shopping_list_collection = mongoClient.get_collection(collection="shoppingLists")

        # First, find the current state of the item
        shopping_list = shopping_list_collection.find_one(
            {"_id": ObjectId(list_id), "items.storeProductId": store_product_id},
            {"items.$": 1}
        )

        if not shopping_list or "items" not in shopping_list or not shopping_list["items"]:
            return jsonify({"error": "Item not found in the list"}), 404

        current_retrieved = shopping_list["items"][0].get("retrieved", False)
        new_value = not current_retrieved

        # Update val to opposite
        result = shopping_list_collection.update_one(
            {
                "_id": ObjectId(list_id),
                "items.storeProductId": store_product_id
            },
            {
                "$set": {
                    "items.$.retrieved": new_value
                }
            }
        )

        if result.matched_count == 0:
            return jsonify({"error": "Item not found in the list"}), 404

        return jsonify({"message": "Item marked as retrieved"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/remove_item_from_list', methods=["PUT"])
def remove_item_from_list():
    try:
        data = request.get_json()
        list_id = data.get("listId")
        store_product_id = data.get("storeProductId")

        if not list_id or not store_product_id:
            return jsonify({"error": "listId and storeProductId are required"}), 400

        shopping_list_collection = mongoClient.get_collection("shoppingLists")

        result = shopping_list_collection.update_one(
            {"_id": ObjectId(list_id)},
            {"$pull": {"items": {"storeProductId": store_product_id}}}
        )

        if result.modified_count == 0:
            return jsonify({"error": "Item not found or already removed"}), 404

        return jsonify({"message": "Item removed from list"}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 
    
@flutter_bp.route('/create_list', methods=["POST"])
def create_list():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request data"}), 400
        
        username = current_user.username
        if not username:
            return jsonify({"error": "Missing user cookie"}), 400
        
        list_name = data.get("listName", "Untitled List") # If no list name is provided, make it untitled

        shopping_list_collection = mongoClient.get_collection(collection="shoppingLists")
        users_collection = mongoClient.get_collection(collection="users")

        # Create the list
        new_list = {
            "listName": list_name,
            "items": [],
            "date": datetime.now(timezone.utc)
        }
        list_insert_result = shopping_list_collection.insert_one(new_list)
        list_id = list_insert_result.inserted_id

        # Update users shoppingListIds
        users_collection.update_one(
            {"username": username},
            {"$push": {"shoppingListIds": list_id}}
        )

        return jsonify({"message": "List created", "listId": str(list_id)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@flutter_bp.route('/delete_list', methods=["DELETE"])
def delete_list():
    try:

        username = current_user.username
        if not username:
            return jsonify({"error": "Missing user cookie"}), 400
        
        data = request.json
        list_id = data.get("listId")

        if not username or not list_id:
            return jsonify({"error": "listId is required"}), 400

        shopping_list_collection = mongoClient.get_collection(collection="shoppingLists")
        users_collection = mongoClient.get_collection(collection="users")

        # Delete the list
        shopping_list_collection.delete_one({"_id": ObjectId(list_id)})

        # Remove from users shoppingListIds
        users_collection.update_one(
            {"username": username},
            {"$pull": {"shoppingListIds": ObjectId(list_id)}}
        )

        return jsonify({"message": "List deleted"}), 200

    except Exception as e:
        return f"An error occurred: {e}", 400

@flutter_bp.route('/signup', methods=['POST'])
@swag_from('../swagger/signup.yml')
def signup():
    '''Add a new user to the usersdb'''
    try:
        collection = mongoClient.get_collection(collection="users")
        
        # Get the JSON data from the request, extract the username, add additional fields
        data = request.json
        query = {"username": str(data["username"])}

        if collection.count_documents(query) > 0:
            e = ClientErrorMessage(message="Username taken. Please try a new one.", detail="Username already exists.")
            return jsonify(e.flutter_response()), 400
        else:
            data["password"] = generate_password_hash(data["password"])
            new_user = User(username=data["username"], password=data["password"])

            collection.insert_one(new_user.get_mongo_entry())
            return jsonify({"message": "User added successfully"}), 200
        
    except Exception as e:
        print("unable to add")
        return f"An error occurred: {e}"

@flutter_bp.route('/login', methods=['POST'])
@swag_from('../swagger/login.yml')
def login():
    '''Login user using username and password'''
    try:
        collection = mongoClient.get_collection(collection="users")
        
        # Get the JSON data from the request
        data = request.json
        query = {"username": str(data["username"])}

        mongo_entry = collection.find_one(query)

        if not mongo_entry:
            e = ClientErrorMessage(message="Username not found.", detail="Username does not match any existing users.")
            return jsonify(e.flutter_response()), 400
        if not check_password_hash(mongo_entry["password"], data["password"]):
            e = ClientErrorMessage(message="Incorrect password.", detail="Username found, password does not match.")
            return jsonify(e.flutter_response()), 400
        else:
            user = User(
                        id=str(mongo_entry["_id"]),
                        username=mongo_entry["username"],
                        password=mongo_entry["password"],
                        receipt_ids= [str(x)for x in mongo_entry["receiptIds"]],
                        shopping_list_ids=[str(x) for x in mongo_entry["shoppingListIds"]],
                        favorite_store_ids=[str(x) for x in mongo_entry["favoriteStoreIds"]]
                        )
            login_user(user)
            return jsonify({'message': 'User logged in', 'user details': user.flutter_response()}), 200
        
    except Exception as e:
        return f"An error occurred: {e}"

@flutter_bp.route('/logout', methods=['POST'])
@login_required
@swag_from('../swagger/logout.yml')
def logout():
    '''Logout user'''
    print(request)
    logout_user()
    return jsonify({"message": "Logout successful"})