import logging
from PIL import Image
from bson import ObjectId
from bson.json_util import loads, dumps
from flask import Blueprint, request, jsonify
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
from mongoClient.mongo_client import MongoConnector
from flask_login import current_user
from FlutterService.ClientErrorMessage import ClientErrorMessage


from AzureDIConnection.DIConnection import analyze_receipt
# from mongoClient.mongo_routes import add_receipt_data

flutter_bp = Blueprint('flutter_bp', __name__)

decode_processor = NameProcessor(prompt_key="DECODE_PROMPT", cache_path="NameProcessing/.decode_cache.json")
map_processor = NameProcessor(prompt_key="MAP_PROMPT", cache_path="NameProcessing/.map_cache.json")

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
    # TODO align with frontend request
    try:
        data = request.get_json()
        scanned_receipt = extract_receipt(data)
        # get product_name list
        product_names = [scanned_line_item.store_product_name for scanned_line_item in scanned_receipt.scanned_line_items]
        # get mapped name list
        generic_names = map_processor.processNames(product_names)

        collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")

        #go through each generic item from api call
        for i, name in enumerate(generic_names):
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
            
            # find existing genericItems in db that are the closest match, and collect their genericNames
            query_results = list(collection.aggregate(agg_pipeline))

            # filter out the results if their matching score is less than 2
            top_generic_names = [result['genericName'] for result in query_results if result['score'] > 2]

            # in the case that no match is found, use the name generated by the api
            if not top_generic_names or top_generic_names == []:
                top_generic_names = [name]

            scanned_receipt.scanned_line_items[i].generic_matches = top_generic_names
                                          
        logging.debug(f"Processed receipt: {scanned_receipt.flutter_response()}")
        return jsonify({'message': 'File successfully uploaded', 'receipt': scanned_receipt.flutter_response()}), 200
       
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
        
        # now add the receipt to the receipt db
        # Access the database and collection
        collection = mongoClient.get_collection(db="receiptdb", collection="receipts")
        receipt_id = collection.insert_one(scanned_receipt.get_mongo_entry()).inserted_id
        
        if current_user.is_authenticated:
            # Add the receipt ID to the user's receipt IDs
            logging.debug(f"User authenticated")
            user_collection = mongoClient.get_collection(db="userdb", collection="users")
            query = {"username": current_user.username}
            current_user.receipt_ids.append(receipt_id)
            update_operation = { '$set' : {'receiptIds' : current_user.receipt_ids}}
            user_collection.update_one(query, update_operation)
            
    
        logging.debug(f"Data from mongo: {receipt_id}")
        
        # update data for dashboard analytics if user is logged in
        if current_user.is_authenticated:
            # get dashboard data from database with user_id
            collection = mongoClient.get_collection(db="dashboarddb", collection="user_dashboard")
            dashboard_data = collection.find_one({"_userId": current_user.get_id()})

            # create Dashboard object
            if dashboard_data:
                dashboard = Dashboard(**dashboard_data)
            else:
                dashboard = Dashboard(current_user.get_id())  # create an empty Dashboard if none exists

            # update dashboard data
            dashboard_manager = DashboardManager()
            dashboard_manager.update_dashboard(dashboard, scanned_receipt)

            # update dashboard in the database
            collection.update_one(
                {"_userId": dashboard._user_id},
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
        
        collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")
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
    collection = mongoClient.get_collection(db="grocerydb", collection="genericItems")

    for scanned_line_item in scanned_receipt.scanned_line_items:

        doccument = collection.find_one({"genericName": scanned_line_item.generic_matches[0]})

        if doccument:
            scanned_line_item.generic_id = doccument["_id"]
        else:
            scanned_line_item.generic_id = collection.insert_one({"genericName": scanned_line_item.generic_matches[0]}).inserted_id

def post_store_products(scanned_receipt):
    '''find/create the product id for the given product'''

    # should call post generic items first, to make sure that each posted product has a generic id
    post_generic_items(scanned_receipt)

    # if the store product is in the db, add the id to the product object, update the recent prices
    # if the store product is not in the db, add the store product to the db and then add the id to the product object
    collection = mongoClient.get_collection(db="grocerydb", collection="storeProducts")

    for scanned_line_item in scanned_receipt.scanned_line_items:

        scanned_line_item.store_name = scanned_receipt.store_name
        scanned_line_item.date = scanned_receipt.date

        if not (scanned_line_item.store_product_name and scanned_line_item.store_name and scanned_line_item.generic_id and scanned_line_item.price_per_count and scanned_line_item.date):
            ValueError("Valid store product required to create a store product")

        query = {"storeProductName": scanned_line_item.store_product_name, "storeName": scanned_receipt.store_name}

        doccument = collection.find_one(query)

        if doccument:
            # if the store product is in the db, add the id to the product object, update the recent prices
            # store the id
            scanned_line_item.id = doccument["_id"]
            # TODO: UPDATE PRICING LOGIC
            prices = doccument["recentPrices"]
            prices.append([scanned_line_item.price_per_count, scanned_receipt.date])
            prices = prices[-5:]
            update_operation = { '$set' : {'recentPrices' : prices}}
            collection.update_one(query, update_operation)
        else:
            # insert the product, set the id
            scanned_line_item.id = collection.insert_one(scanned_line_item.first_mongo_entry()).inserted_id

@flutter_bp.route('/get_dashboard_data/<user_id>', methods=["GET"])
def get_dashboard_data(user_id):
    try:
        collection = mongoClient.get_collection(db="dashboarddb", collection="dashboard")
        user_dashboard_data = collection.find_one({"_userId": user_id}, {'_id': 0}) # each user has one dashboard
        if user_dashboard_data:
            return jsonify(user_dashboard_data), 200
        else:
            # user has not uploaded any receipts yet
            return jsonify({"message": "No dashboard data available yet."}), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

@flutter_bp.route('/signup', methods=['POST'])
@swag_from('../swagger/signup.yml')
def signup():
    '''Add a new user to the usersdb'''
    try:
        collection = mongoClient.get_collection(db="userdb", collection="users")
        
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
        collection = mongoClient.get_collection(db="userdb", collection="users")
        
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