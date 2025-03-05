import sys
import os
import mongomock
from pymongo import MongoClient

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app 
import pytest

@pytest.fixture
def mock_db():
    """A mock MongoDB database."""
    with mongomock.patch():
        mock_db = MongoClient()
        yield mock_db

@pytest.fixture
def client(mock_db):
    """A test client for the app."""
    with app.test_client() as client:
        yield client

def test_add_user(client, mock_db):
    """Test the home route."""
    response = client.post('/auth/signup', json=dict(id='test_suite_user', password='test_suite_password'))
    assert response.status_code == 200
    assert "message" in response.json, "Data added successfully"
    assert mock_db["user_db"]["users"].find_one({'id':'test_suite_user', 'password':'test_suite_password'}) is not None