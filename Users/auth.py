import os
from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from
from .User import User
from mongoClient.mongo_client import MongoConnector

auth_bp = Blueprint('auth_bp', __name__)
mongoClient = MongoConnector()

@auth_bp.route('/signup', methods=['POST'])
@swag_from('../swagger/signup.yml')
def signup():
    '''Add a new user to the usersdb'''
    try:
        collection = mongoClient.get_collection(collection="users")
        
        # Get the JSON data from the request, extract the username, add additional fields
        data = request.json
        query = {"username": str(data["username"])}

        if collection.count_documents(query) > 0:
            return jsonify({"message": "User id already exists"})
        else:
            data["password"] = generate_password_hash(data["password"])
            new_user = User(username=data["username"], password=data["password"])

            collection.insert_one(new_user.get_mongo_entry())
            return jsonify({"message": "User added successfully"})
        
    except Exception as e:
        print("unable to add")
        return f"An error occurred: {e}"

@auth_bp.route('/login', methods=['POST'])
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
            return jsonify({"message": "Username not found"})
        
        if not check_password_hash(mongo_entry["password"], data["password"]):
            return jsonify({"message": "Incorrect password"})
        else:
            login_user(User(username=mongo_entry["username"], password=mongo_entry["password"], receipt_ids=mongo_entry["receiptIds"], shopping_list_ids=mongo_entry["shoppingListIds"], favorite_store_ids=mongo_entry["favoriteStoreIds"]))
            return jsonify({"message": "Login successful"})
        
    except Exception as e:
        return f"An error occurred: {e}"

@auth_bp.route('/logout', methods=['POST'])
@swag_from('../swagger/logout.yml')
def logout():
    '''Logout user'''
    logout_user()
    return jsonify({"message": "Logout successful"})