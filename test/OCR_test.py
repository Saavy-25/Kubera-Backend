import pytest
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Grocery.ScannedReceipt import ScannedReceipt
from AzureDIConnection.DIConnection import analyze_receipt
from app import app

@pytest.fixture
def client():
    client = app.test_client()
    yield client

def test_process_receipt():
    '''test that receipt object can be built from image'''
    receipt = analyze_receipt("test/test_receipt.jpg")
    
    assert receipt.store_name == "TRADER JOE'S"
    assert receipt.store_address == '3724 SW Archer Road, Gainesville, FL, 32608'
    assert receipt.date == "2025-02-25"
    assert receipt.total_receipt_price == 57.12
    assert len(receipt.scanned_line_items) == 14

def test_count_detection():
    '''test that line items are read in receipt processing'''
    receipt = analyze_receipt("test/test_receipt.jpg")
    rice = receipt.scanned_line_items[0]
    
    assert rice.line_item == "BUTTER CHICKEN W/BASMATI"
    assert rice.count == 2
    assert rice.total_price == 8.98

def test_process_receipt_route(client):
    '''test that the process_receipt route works'''
    data = {
        'file': open('test/test_receipt.jpg', 'rb')
    }

    response = client.post('/flutter/process_receipt', content_type='multipart/form-data', data=data)

    assert response.status_code == 200
    receipt_map = response.json['receipt']
    assert receipt_map['storeName'] == "TRADER JOE'S"
    assert receipt_map['storeAddress'] == '3724 SW Archer Road, Gainesville, FL, 32608'
    assert receipt_map['date'] == "2025-02-25"
    assert receipt_map['totalReceiptPrice'] == 57.12

    rice = receipt_map['scannedLineItems'][0]
    
    assert rice['lineItem'] == "BUTTER CHICKEN W/BASMATI"
    assert rice['count'] == 2
    assert rice['totalPrice'] == 8.98

