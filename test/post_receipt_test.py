import pytest
import sys
import os
import json


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from Grocery.StoreProduct import StoreProduct
from Grocery.Receipt import Receipt
from FlutterService.flutter_routes import post_generic_items, post_store_products

@pytest.fixture
def client():
    client = app.test_client()
    yield client

# def test_post_generic_items():
#     try:
#         product = StoreProduct(line_item="SPR STRAWB JAM", count=2, total_price=10.0, store_product_name="Spring Strawberry Jam", generic_matches=["Strawbery Jam"])
#         receipt = Receipt(store_name="TRADER JOE'S", store_address={'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'}, total_receipt_price=57.12, date="2025-02-25", products=[product])

#         post_generic_items(receipt)

#         assert True
#     except:
#         assert False

# def test_post_store_product():
#     try:
#         product = StoreProduct(line_item="SPR STRAWB JAM", count=2, total_price=10.0, store_product_name="Spring Strawberry Jam", generic_matches=["Strawbery Jam"])
#         receipt = Receipt(store_name="TRADER JOE'S", store_address={'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'}, total_receipt_price=57.12, date="2025-02-25", products=[product])

#         post_store_products(receipt)
        
#         assert True
#     except:
#         assert False


def test_post_receipt(client):
    product = StoreProduct(line_item="SPR STRAWB JAM", count=2, total_price=10.0, store_product_name="Spring Strawberry Jam", generic_matches=["Strawbery Jam"])
    receipt = Receipt(store_name="TRADER JOE'S", store_address={'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'}, total_receipt_price=57.12, date="2025-02-25", products=[product])
    try:
        data=json.dumps(receipt.get_map())
    except:
        ValueError, "cannot make json obj"

    response = client.post('/flutter/post_receipt', data=data, content_type='application/json')

    assert response.status_code == 200