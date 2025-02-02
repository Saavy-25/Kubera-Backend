import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

import configparser

endpoint = "https://kubera-doc-inteli.cognitiveservices.azure.com/"
PublixReceipt = "PublixReceipt.jpg"
TraderJoesReceipt = "TraderJoesReceipt.jpg"
WalmartReceipt = "WalmartReceipt.jpg"

# from:
# https://github.com/Azure-Samples/document-intelligence-code-samples/blob/main/Python(v4.0)/Prebuilt_model/sample_analyze_receipts.py
def format_price(price_dict):
    return "".join([f"{p}" for p in price_dict.values()])

# sample document, convert to bytes
def convertBytes(fileName):
    with open(fileName, "rb") as image:
        f = image.read()
        b = bytearray(f)

# get key from .ini file
def getKey(resource, secret):
    config = configparser.ConfigParser()
    config.read('../config.ini')
    key = config[resource][secret]

# Base code from:
# https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/how-to-guides/use-sdk-rest-api?view=doc-intel-4.0.0&tabs=windows&pivots=programming-language-python
def analyze_receipts():

    client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(getKey('AzureDocInteli', 'resource_key'))
    )
    poller = client.begin_analyze_document(
        "prebuilt-receipt", AnalyzeDocumentRequest(bytes_source=convertBytes(PublixReceipt)), locale="en-US"
    )
    receipts: AnalyzeResult = poller.result()

    if receipts.documents:
        for idx, receipt in enumerate(receipts.documents):
            print(f"--------Analysis of receipt #{idx + 1}--------")
            print(f"Receipt type: {receipt.doc_type if receipt.doc_type else 'N/A'}")
            if receipt.fields:
                merchant_name = receipt.fields.get("MerchantName")
                if merchant_name:
                    print(
                        f"Merchant Name: {merchant_name.get('valueString')} has confidence: "
                        f"{merchant_name.confidence}"
                    )
                transaction_date = receipt.fields.get("TransactionDate")
                if transaction_date:
                    print(
                        f"Transaction Date: {transaction_date.get('valueDate')} has confidence: "
                        f"{transaction_date.confidence}"
                    )
                items = receipt.fields.get("Items")
                if items:
                    print("Receipt items:")
                    for idx, item in enumerate(items.get("valueArray")):
                        print(f"...Item #{idx + 1}")
                        item_description = item.get("valueObject").get("Description")
                        if item_description:
                            print(
                                f"......Item Description: {item_description.get('valueString')} has confidence: "
                                f"{item_description.confidence}"
                            )
                        item_quantity = item.get("valueObject").get("Quantity")
                        if item_quantity:
                            print(
                                f"......Item Quantity: {item_quantity.get('valueString')} has confidence: "
                                f"{item_quantity.confidence}"
                            )
                        item_total_price = item.get("valueObject").get("TotalPrice")
                        if item_total_price:
                            print(
                                f"......Total Item Price: {format_price(item_total_price.get('valueCurrency'))} has confidence: "
                                f"{item_total_price.confidence}"
                            )
                subtotal = receipt.fields.get("Subtotal")
                if subtotal:
                    print(
                        f"Subtotal: {format_price(subtotal.get('valueCurrency'))} has confidence: {subtotal.confidence}"
                    )
                tax = receipt.fields.get("TotalTax")
                if tax:
                    print(f"Total tax: {format_price(tax.get('valueCurrency'))} has confidence: {tax.confidence}")
                tip = receipt.fields.get("Tip")
                if tip:
                    print(f"Tip: {format_price(tip.get('valueCurrency'))} has confidence: {tip.confidence}")
                total = receipt.fields.get("Total")
                if total:
                    print(f"Total: {format_price(total.get('valueCurrency'))} has confidence: {total.confidence}")
            print("--------------------------------------")



if __name__ == "__main__":
    analyze_receipts()