import io
import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from dotenv import load_dotenv
# Import the models
from Grocery.ScannedLineItem import ScannedLineItem
from Grocery.ScannedReceipt import ScannedReceipt

ENDPOINT = "https://kubera-doc-inteli.cognitiveservices.azure.com/"
ADDRESS_COMPONENTS = ["streetAddress", "city", "state", "postalCode"]

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
                print(type(transaction_date))
                address_map = receipt.fields.get("MerchantAddress").get('valueAddress')

                address = []
                if address_map:
                    for component in ADDRESS_COMPONENTS:
                        if address_map.get(component):
                            address.append(address_map.get(component))
                
                address = ', '.join(address)
                
                total = receipt.fields.get("Total").get('valueCurrency').get('amount')

                items = receipt.fields.get("Items")
                scanned_line_items = []

                if items:
                    for item in items.get("valueArray"):
                        
                        #get the line item (abreviated name)
                        item_description = item.get("valueObject").get("Description")

                        if item_description:
                            item_description = item_description.get('valueString')
                        else:
                            item_description = "None"
                        
                        # get the count of items associated with the line items, set to 1 if not detected
                        count = item.get("valueObject").get("Quantity")

                        if count:
                             count = count.get('valueNumber')
                        else:
                            count = 1
                            
                        # get the total price for the line item
                        item_total_price = item.get("valueObject").get("TotalPrice")

                        if item_total_price:
                            item_total_price = item_total_price.get('valueCurrency').get('amount')
                        else:
                            item_total_price = 0.0

                        scanned_line_items.append(ScannedLineItem(line_item=item_description, count=count, total_price=item_total_price))

                return ScannedReceipt(store_name=merchant_name, date=transaction_date, store_address=address, total_receipt_price=total, scanned_line_items=scanned_line_items)
