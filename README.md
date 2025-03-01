## Getting Started

Run 'pip install -r requirements.txt'

Run DevSetUp.py

Add MONGO_URI to the generated .env file. 
Get your mongoDB connection string from mongoDB Atlas. Make sure you put in the correct username and password. 

Add AZURE_RESOURCE_KEY to the .env file.

Add the Mongo_URI and the AZURE_RESOURCE_KEY to the generated Dockerfile.

## Viewing Doccumentation

View Swagger Doccumentation for API but running app.py and visiting http://127.0.0.1:5000/apidocs/

## Building a Docker Image

Make sure to download and begin running Docker on your device.

Run "docker build . --file Dockerfile --tag my-image-name:$(date +%s)"
