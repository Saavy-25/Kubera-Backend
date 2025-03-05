## Getting Started

Run the following commands to set up local development environment

`'pip install -r requirements.txt'

`python DevSetUp.py

Add MONGO_URI to your .env file. 
Get your mongoDB connection string from mongoDB Atlas. Make sure you put in the correct username and password.

Add in images "PublixReceipt.jpg", "TraderJoes.jpg" "SamsReceipt.jpg" and "WalmartReceipt.jpg" to the AzureDIConnection directory before running DIConnection.py file.

## Doccumentation

View Swagger Doccumentation for API during local dev by running app.py and visiting http://127.0.0.1:5000/apidocs/

## Deployment

Currently deployed code is on prod branch. 

Backend is currently deployed on Azure App Service. When running, the following endpoints can be accessed:

application: https://kubera-avbyczbee5fybnht.eastus2-01.azurewebsites.net/

doccumentation: https://kubera-avbyczbee5fybnht.eastus2-01.azurewebsites.net/apidocs/
