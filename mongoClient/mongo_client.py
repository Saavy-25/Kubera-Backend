import os
from pymongo import MongoClient
import certifi

# Set up MongoDB URI from environment variable
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

# Initialize the MongoDB client Object
mongoClient = MongoClient(mongo_uri, tlsCAFile=certifi.where())
