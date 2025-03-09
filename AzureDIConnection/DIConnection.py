import io
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
# Import the models
from Grocery.StoreProduct import StoreProduct
from Grocery.Receipt import Receipt

ENDPOINT = "https://kubera-doc-inteli.cognitiveservices.azure.com/"
PUBLIXRECEIPT = "PublixReceipt.jpg"
TRADERJOESRECEIPT = "TraderJoesReceipt.jpg"
WALMARTRECEIPT = "WalmartReceipt.jpg"
SAMSRECEIPT = "SamsReceipt.jpg"

# sample document, convert to bytes
def convert_bytes(file):
    '''convert file type to byte string'''
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
def get_key():
    '''get the Azure resource key'''
    load_dotenv()
    return os.getenv("AZURE_RESOURCE_KEY")

# Base code from:
# https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&tabs=windows&pivots=programming-language-python

def analyze_receipt(r):
    '''create receipt object from receipt scan'''
    client = DocumentIntelligenceClient(endpoint=ENDPOINT, credential=AzureKeyCredential(get_key()))

    poller = client.begin_analyze_document("prebuilt-receipt", AnalyzeDocumentRequest(bytes_source=convert_bytes(r)), locale="en-US")
    receipts: AnalyzeResult = poller.result()

    if receipts.documents:
        for receipt in receipts.documents:
            if receipt.fields:
                merchant_name = receipt.fields.get("MerchantName").get('valueString')
                transaction_date = receipt.fields.get("TransactionDate").get('valueDate')
                address = receipt.fields.get("MerchantAddress").get('valueAddress')
                total = receipt.fielfs.get("Total").get('valueCurrency').get('amount')

                items = receipt.fields.get("Items")
                products = []

                if items:
                    for item in items.get("valueArray"):
                        
                        item_description = item.get("valueObject").get("Description")

                        if item_description:
                            item_description = item_description.get('valueString')
                        else:
                            item_description = "None"
                        
                        count = item.get("valueObject").get("Quantity")

                        if count:
                             count = count.get('valueNumber')
                        else:
                            count = "None"
                        
                        unit = item.get("valueObject").get("QuantityUnit")

                        # if unit:
                        #     unit = unit.get('valueString')
                        # else:
                        #     unit = "None"
                        
                        unit_price = item.get("valueObject").get("Price")

                        if unit_price:
                            unit_price = unit_price.get('valueCurrency').get('amount')
                        else:
                            unit_price = "None"
                        
                        item_total_price = item.get("valueObject").get("TotalPrice")

                        if item_total_price:
                            item_total_price = item_total_price.get('valueCurrency').get('amount')
                        else:
                            item_total_price = "None"

                        products.append(StoreProduct(line_item=item_description, count=count, unit=unit, unit_price=unit_price, total_price=item_total_price))

                return Receipt(store_name=merchant_name, date=transaction_date, store_address=address, total_receipt_price=total, products=products)