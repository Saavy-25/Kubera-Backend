import os
from pymongo import MongoClient
import certifi
from dotenv import load_dotenv
load_dotenv(override=True)

class MongoConnector:
    # Single connection instance
    _instance = None

    def __new__(cls, uri=os.getenv("MONGO_URI")):
        if cls._instance is None:
            cls._instance = super(MongoConnector, cls).__new__(cls)
            cls._instance.client = MongoClient(uri, tlsCAFile=certifi.where())
            cls._instance.db = None
            cls._instance.collection = None
        return cls._instance
    
    def set_db(self, db_name):
        self.db = self.client[db_name]
    
    def get_collection(self, collection):
        # Returns a reference to a specific collection to avoid race condition
        if self.db is None:
            raise Exception("Database not set. set_db(db_name) should have been called during initialization.")
        return self.db[collection]

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None