import re
from datetime import datetime

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, Flask!"


@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    formatted_now = now.strftime("%a, %d %b, %Y at %X")

    content = "Hello there, " + name + "! It's " + formatted_now
    return content
