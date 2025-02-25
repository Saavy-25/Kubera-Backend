import os
from flask import Blueprint, jsonify, request
from pymongo import MongoClient
import certifi
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flasgger import Swagger, swag_from
from .User import User
from mongoClient.mongo_client import mongoClient

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/signup', methods=['POST'])
@swag_from('../swagger/signup.yml')
def signup():
    '''Add a new user to the usersdb'''
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["userdb"]
        collection = db["users"]
        
        # Get the JSON data from the request, extract the username, add additional fields
        data = request.json
        query = {"username": str(data["username"])}
        data["receiptIds"] = []
        data["listIds"] = []
        data["password"] = generate_password_hash(data["password"])

        if collection.count_documents(query) >= 1:
            return jsonify({"message": "User id already exists"})
        else:
            result = collection.insert_one(data)
            return jsonify({"message": "Data added successfully", "id": str(result.inserted_id)})
        
    except Exception as e:
        print("unable to add")
        return f"An error occurred: {e}"

@auth_bp.route('/login', methods=['GET'])
@swag_from('../swagger/login.yml')
def login():
    '''Login user using username and password'''
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["userdb"]
        collection = db["users"]
        
        # Get the JSON data from the request
        data = request.json
        query = {"username": str(data["username"])}

        mongo_entry = collection.find_one(query)

        if not mongo_entry:
            return jsonify({"message": "Username not found"})
        
        if not check_password_hash(mongo_entry["password"], data["password"]):
            return jsonify({"message": "Incorrect password"})
        else:
            login_user(User(username=mongo_entry["username"], pw=mongo_entry["password"], receipts=mongo_entry["receiptIds"], lists=mongo_entry["listIds"]))
            return jsonify({"message": "Login successful"})
        
    except Exception as e:
        return f"An error occurred: {e}"

@auth_bp.route('/logout')
@swag_from('../swagger/logout.yml')
def logout():
    '''Logout user'''
    logout_user()
    return jsonify({"message": "Logout successful"})