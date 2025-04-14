import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    client = app.test_client()
    yield client

def test_checked_toggle(client):
    insert_data = {
        "listId": "67fd3dc45f83f8bd5d0aaaba",
        "storeProductId": "67f95a83c401ccc1e34f2710",
        "productName": "Brussels Sprouts 1 Pound"
    }

    response = client.post('/flutter/add_item_to_list', data=insert_data)
    assert response.status_code == 200

    toggle_data = {
        "listId": "67fd3dc45f83f8bd5d0aaaba",
        "storeProductId": "67f95a83c401ccc1e34f2710"
    }
    response = client.put('flutter/toggle_list_item', data=toggle_data)