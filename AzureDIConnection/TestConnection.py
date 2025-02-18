import io
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

from dotenv import load_dotenv

import sys

# Add the parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the modules
from Grocery.StoreProduct import StoreProduct
from Grocery.Receipt import Receipt

endpoint = "https://kubera-doc-inteli.cognitiveservices.azure.com/"
PublixReceipt = "PublixReceipt.jpg"
TraderJoesReceipt = "TraderJoesReceipt.jpg"
WalmartReceipt = "WalmartReceipt.jpg"
SamsReceipt = "SamsReceipt.jpg"

# sample document, convert to bytes
def convertBytes(file):
    if isinstance(file, str):
        with open(file, "rb") as image:
            f = image.read()
            b = bytearray(f)
    elif isinstance(file, io.BytesIO):
        file.seek(0)
        b = bytearray(file.read())
    else: 
        raise TypeError("Invalid input type. Expected str or io.BytesIO.")
    return b

# get key from .env file
def getKey():
    load_dotenv()
    return os.getenv("AZURE_RESOURCE_KEY")

# Base code from:
# https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&tabs=windows&pivots=programming-language-python
def analyze_receipts(r):
    client = DocumentIntelligenceClient(endpoint=endpoint, credential=AzureKeyCredential(getKey()))

    poller = client.begin_analyze_document("prebuilt-receipt", AnalyzeDocumentRequest(bytes_source=convertBytes(r)), locale="en-US")
    receipts: AnalyzeResult = poller.result()

    if receipts.documents:
        for idx, receipt in enumerate(receipts.documents):
            if receipt.fields:
                merchant_name = receipt.fields.get("MerchantName").get('valueString')
                transaction_date = receipt.fields.get("TransactionDate").get('valueDate')

                items = receipt.fields.get("Items")
                products = []

                if items:
                    for idx, item in enumerate(items.get("valueArray")):
                        
                        item_description = item.get("valueObject").get("Description")

                        if item_description:
                            item_description = item_description.get('valueString')
                        else:
                            "None"
                        
                        item_quantity = item.get("valueObject").get("Quantity")

                        if item_quantity:
                            item_quantity = item_quantity.get('valueString')
                        else:
                            "None"
                        
                        item_total_price = item.get("valueObject").get("TotalPrice")

                        if item_total_price:
                            item_total_price = item_total_price.get('valueCurrency').get('amount')
                        else:
                            "None"

                        products.append(StoreProduct(product_name=item_description, unit=item_quantity, price=item_total_price, date=transaction_date))

                return Receipt(store_name=merchant_name, date=transaction_date, products=products)

if __name__ == "__main__":
    r = analyze_receipts(SamsReceipt)
    r.print()