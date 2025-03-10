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
        'store_name': "TRADER JOE'S",
        'products': [{'line_item': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'total_price': 8.98}],
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_store_name(client):
    data = {
        'date': "2025-02-25",
        'products': [{'line_item': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'total_price': 8.98}],
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_store_address(client):
    data = {
        'store_name': "TRADER JOE'S",
        'date': "2025-02-25",
        'products': [{'line_item': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'total_price': 8.98}],
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_total_price(client):
    data = {
        'store_name': "TRADER JOE'S",
        'date': "2025-02-25",
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'products': [{'line_item': "BUTTER CHICKEN W/BASMATI", 'count': 2, 'total_price': 8.98}],
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_mapping_missing_products(client):
    data = {
        'store_name': "TRADER JOE'S",
        'date': "2025-02-25",
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_none_required_field(client):
    data = {
        'store_name': None,
        'date': "2025-02-25",
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500

def test_empty_string_required_field(client):
    data = {
        'store_name': "",
        'date': "2025-02-25",
        'store_address': {'houseNumber': '3724', 'road': 'SW Archer Road', 'postalCode': '32608', 'city': 'Gainesville', 'state': 'FL', 'streetAddress': '3724 SW Archer Road'},
        'total_receipt_price': 57.12
    }

    response = client.post('/flutter/map_receipt', data=data)

    assert response.status_code == 500