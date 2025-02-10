import logging

from flask import Flask
from dotenv import load_dotenv
from mongoClient.mongo_routes import mongo_bp 
from FlutterService.flutter_routes import flutter_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def home():
    return "Hello, Flask!"

# Register Blueprints
app.register_blueprint(mongo_bp, url_prefix='/mongo')
app.register_blueprint(flutter_bp, url_prefix='/flutter')

if __name__ == "__main__":
    app.run(debug=True)
