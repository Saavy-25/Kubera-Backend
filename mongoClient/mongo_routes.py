import os
from bson import ObjectId
from flask import Blueprint, jsonify, request
from pymongo import MongoClient
import certifi
import pymongo
from dotenv import load_dotenv
from mongoClient.mongo_client import mongoClient

# Define mongoDB Blueprint
mongo_bp = Blueprint('mongo_bp', __name__)

@mongo_bp.route('/test-mongo')
def test_mongo():
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        mongoClient.admin.command("ping")  # This will raise an exception if connection fails
        return 'MongoDB connection successful!'
    except pymongo.errors.ConnectionFailure as e:
        return f"MongoDB connection failed: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

@mongo_bp.route('/get-data')
def get_data():
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["grocery-db"]
        collection = db["store-product"]
        
        # Perform a query (e.g., find all documents)
        data = collection.find()
        
        # Convert the data to a list and return as JSON
        data_list = list(data)
        for item in data_list:
            item["_id"] = str(item["_id"])  # Convert ObjectId to string for JSON serialization
        
        return jsonify(data_list)
    except Exception as e:
        return f"An error occurred: {e}"

@mongo_bp.route('/add-data', methods=['POST'])
def add_data():
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["Test"]
        collection = db["items"]
        
        # Get the JSON data from the request
        data = request.json
        
        # Insert the data into the collection
        result = collection.insert_one(data)

        return jsonify({"message": "Data added successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return f"An error occurred: {e}"

@mongo_bp.route('/update-data/<id>', methods=['PUT'])
def update_data(id):
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["Test"]
        collection = db["items"]
        
        # Get the JSON data from the request
        data = request.json
        
        # Update the document in the collection
        result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        
        if result.matched_count == 0:
            return jsonify({"message": "No document found with the given ID"}), 404
        
        return jsonify({"message": "Data updated successfully"})
    except Exception as e:
        return f"An error occurred: {e}"

@mongo_bp.route('/delete-data/<id>', methods=['DELETE'])
def delete_data(id):
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["Test"]
        collection = db["items"]
        
        # Delete the document from the collection
        result = collection.delete_one({"_id": ObjectId(id)})
        
        if result.deleted_count == 0:
            return jsonify({"message": "No document found with the given ID"}), 404
        
        return jsonify({"message": "Data deleted successfully"})
    except Exception as e:
        return f"An error occurred: {e}"
    