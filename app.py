import os
import logging

from flask import Flask, jsonify
from pymongo import MongoClient
import certifi
import pymongo
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Set up MongoDB URI from environment variable
mongo_uri = os.getenv("MONGO_URI")
app.config["MONGO_URI"] = mongo_uri

try:
    mongoClient = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    logging.debug("MongoDB connection initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing MongoDB connection: {e}")
    mongoClient = None

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route('/test-mongo')
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

@app.route('/get-data')
def get_data():
    try:
        if mongoClient is None:
            raise ValueError("MongoDB connection is not initialized")
        
        # Access the database and collection
        db = mongoClient["sample_restaurants"]
        collection = db["neighborhoods"]
        
        # Perform a query (e.g., find all documents)
        data = collection.find()
        
        # Convert the data to a list and return as JSON
        data_list = list(data)
        for item in data_list:
            item["_id"] = str(item["_id"])  # Convert ObjectId to string for JSON serialization
        
        return jsonify(data_list)
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    app.run(debug=True)
