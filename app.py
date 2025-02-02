import os
import logging

from flask import Flask, jsonify
from flask_pymongo import PyMongo
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
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

logging.debug(f"MONGO_URI: {mongo_uri}")

app.config["MONGO_URI"] = mongo_uri
try:
    mongo = PyMongo(app, tlsCAFile=certifi.where())
    logging.debug("MongoDB connection initialized successfully.")
except Exception as e:
    logging.error(f"Error initializing MongoDB connection: {e}")
    mongo = None

@app.route("/")
def home():
    return "Hello, Flask!"

@app.route('/test-mongo')
def test_mongo():
    try:
        if mongo is None or mongo.db is None:
            raise ValueError("MongoDB connection is not initialized")
        mongo.db.command("ping")  # This will raise an exception if connection fails
        return '✅ MongoDB connection successful!'
    except pymongo.errors.ConnectionFailure as e:
        return f"❌ MongoDB connection failed: {e}"
    except Exception as e:
        return f"❌ An error occurred: {e}"

if __name__ == "__main__":
    app.run(debug=True)
