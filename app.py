import os
import logging
import secrets
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv() # Load before access

from flask_login import LoginManager
from flasgger import Swagger
from mongoClient.mongo_routes import mongo_bp
from mongoClient.mongo_client import MongoConnector
from Users.auth import auth_bp
from Users.User import User
from FlutterService.flutter_routes import flutter_bp


# Initialize flask app and swagger page
app = Flask(__name__)

CORS(app)
app.config['SWAGGER'] = {
    'title': 'Kubera API',
    "specs": [
        {
            "endpoint": 'apis',
            "route": '/apis'
        }
    ],
}
swagger = Swagger(app)

# Set secret key for session management
app.secret_key = secrets.token_hex(16)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.ERROR) # Suppress pymongo logging

# If running on Azure App Service, dynamically set prod/dev
ENV = "prod"
AZURE_DEPLOYMENT = 'WEBSITE_HOSTNAME' in os.environ

if AZURE_DEPLOYMENT:
    app.config['ENV'] = 'production'
    app.config['DEBUG'] = False
else:
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    ENV = "dev"

mongoClient = MongoConnector()
mongoClient.set_db(ENV)

@app.route("/")
def home():
    return "Hello, Flask!" 


# Initialize login object
login_manager = LoginManager()
login_manager.init_app(app)

# Callback required by the manager
@login_manager.user_loader
def load_user(username):
    '''Function required by LoginManager'''
    collection = mongoClient.get_collection(collection="users")
    query = {"username": username}
    mongo_entry = collection.find_one(query)
    return User(id=str(mongo_entry["_id"]), username=mongo_entry["username"], password=mongo_entry["password"], receipt_ids=mongo_entry["receiptIds"], shopping_list_ids=mongo_entry["shoppingListIds"], favorite_store_ids=mongo_entry["favoriteStoreIds"])

# Register blueprints
app.register_blueprint(mongo_bp, url_prefix='/mongo')
app.register_blueprint(flutter_bp, url_prefix='/flutter')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)