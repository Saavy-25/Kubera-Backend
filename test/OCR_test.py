import pytest
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Grocery.Receipt import Receipt
from AzureDIConnection.DIConnection import analyze_receipt

def test_process_receipt():
    '''test that receipt object can be built from image'''
    receipt = analyze_receipt("test/test_receipt.jpg")
    
    assert receipt.store_name == "TRADER JOE'S"
    assert receipt.store_address == {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'}
    assert receipt.date == "2025-02-25"
    assert receipt.total_receipt_price == 57.12
    assert len(receipt.products) == 14

def test_count_detection():
    '''test that line items are read in receipt processing'''
    receipt = analyze_receipt("test/test_receipt.jpg")
    rice = receipt.products[0]
    
    assert rice.line_item == "BUTTER CHICKEN W/BASMATI"
    assert rice.count == 2
    assert rice.total_price == 8.98