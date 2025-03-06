from bson import ObjectId
from flask import Blueprint, jsonify, request
import pymongo
from mongoClient.mongo_client import MongoConnector

# Define mongoDB Blueprint
mongo_bp = Blueprint('mongo_bp', __name__)
mongoClient = MongoConnector()

@mongo_bp.route('/test-mongo')
def test_mongo():
    try:
        mongoClient.client.admin.command("ping")  # This will raise an exception if connection fails
        return 'MongoDB connection successful!'
    except pymongo.errors.ConnectionFailure as e:
        return f"MongoDB connection failed: {e}"
    except Exception as e:
        return f"An error occurred: {e}", 400

@mongo_bp.route('/get_data')
def get_data():
    try:
        # Access the database and collection
        collection = mongoClient.get_collection(db="testdb", collection="items")
    
        data = collection.find()
        
        # Convert the data to a list and return as JSON
        data_list = list(data)
        for item in data_list:
            item["_id"] = str(item["_id"])
            item["_id"] = str(item["_id"])
        
        return jsonify(data_list), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

@mongo_bp.route('/add_data', methods=['POST'])
def add_data():
    try:
        collection = mongoClient.get_collection(db="testdb", collection="items")
        
        # Get the JSON data from the request
        data = request.json
        
        # Insert the data into the collection
        result = collection.insert_one(data)

        return jsonify({"message": "Data added successfully", "id": str(result.inserted_id)}), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

@mongo_bp.route('/update_data/<id>', methods=['PUT'])
def update_data(id):
    try:
        collection = mongoClient.get_collection(db="testdb", collection="items")
        
        # Get the JSON data from the request
        data = request.json
        
        # Update the document in the collection
        result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        
        if result.matched_count == 0:
            return jsonify({"message": "No document found with the given ID"}), 404
        
        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        return f"An error occurred: {e}", 400

@mongo_bp.route('/delete_data/<id>', methods=['DELETE'])
def delete_data(id):
    try:
        collection = mongoClient.get_collection(db="testdb", collection="items")
        
        # Delete the document from the collection
        result = collection.delete_one({"_id": ObjectId(id)})
        
        if result.deleted_count == 0:
            return jsonify({"message": "No document found with the given ID"}), 404
        
        return jsonify({"message": "Data deleted successfully"}), 200
    except Exception as e:
        return f"An error occurred: {e}", 400