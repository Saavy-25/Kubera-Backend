import pytest
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    client = app.test_client()
    yield client

def test_mapping_missing_date(client):
    data = {
        'storeName': "TRADER JOE'S",
        'products': [{'lineItem': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'totalPrice': 8.98}],
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_store_name(client):
    data = {
        'date': "2025-02-25",
        'products': [{'lineItem': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'totalPrice': 8.98}],
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_store_address(client):
    data = {
        'storeName': "TRADER JOE'S",
        'date': "2025-02-25",
        'products': [{'lineItem': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'totalPrice': 8.98}],
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_total_price(client):
    data = {
        'store_name': "TRADER JOE'S",
        'date': "2025-02-25",
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'products': [{'lineItem': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'totalPrice': 8.98}],
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_products(client):
    data = {
        'storeName': "TRADER JOE'S",
        'date': "2025-02-25",
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_none_required_field(client):
    data = {
        'storeName': None,
        'date': "2025-02-25",
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_empty_string_required_field(client):
    data = {
        'storeName': "",
        'date': "2025-02-25",
        'storeAddress': '3724 SW Archer Road, Gainesville, FL, 32608',
        'totalReceiptPrice': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500