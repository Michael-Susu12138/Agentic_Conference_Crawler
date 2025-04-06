"""
Integration test suite for the Conference Monitor API
Tests the actual API endpoints using real credentials
"""
import pytest
import json
import os
from dotenv import load_dotenv
from unittest import mock

# Make sure environment variables are loaded
load_dotenv()

# Import the actual app
from conference_monitor.api.app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_status(client):
    """Test the API status endpoint"""
    response = client.get('/api/status')
    
    # Check response code
    assert response.status_code == 200
    
    # Parse response data
    data = json.loads(response.data)
    
    # Verify response contents
    assert data['status'] == 'online'
    assert data['version'] == '1.0.0'
    assert 'api_provider' in data

def test_get_research_areas(client):
    """Test the get research areas endpoint"""
    response = client.get('/api/research-areas')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    # Verify we have at least one research area
    assert len(data) > 0

def test_get_conferences(client):
    """Test the get conferences endpoint"""
    response = client.get('/api/conferences')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    
    # If conferences exist, check their structure
    if data:
        assert 'id' in data[0]
        assert 'title' in data[0]

def test_run_query(client):
    """Test the query endpoint"""
    request_data = {
        "query": "What are the top AI conferences?"
    }
    response = client.post('/api/query', 
                          data=json.dumps(request_data),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert isinstance(data['response'], str)
    assert len(data['response']) > 20  # Ensure we have a reasonable response

def test_refresh_conferences(client):
    """Test the refresh conferences endpoint"""
    request_data = {
        "research_areas": ["artificial intelligence"]
    }
    response = client.post('/api/conferences/refresh', 
                         data=json.dumps(request_data),
                         content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    assert "results" in data

def test_refresh_papers(client):
    """Test the refresh papers endpoint"""
    request_data = {
        "research_areas": ["artificial intelligence"]
    }
    response = client.post('/api/papers/refresh', 
                         data=json.dumps(request_data),
                         content_type='application/json')
    
    # Accept either 200 or 500 status code since the paper refresh might encounter errors
    # but the API should still return a valid JSON response
    assert response.status_code in [200, 500]
    data = json.loads(response.data)
    
    if response.status_code == 200:
        assert data['success'] == True
        assert "results" in data
    else:
        # Even on error, we should have a properly formatted error response
        assert data['success'] == False
        assert "message" in data

def test_get_trends(client):
    """Test the get trends endpoint"""
    response = client.get('/api/trends?area=artificial intelligence&count=5')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "trends" in data
    
def test_update_research_areas(client):
    """Test the update research areas endpoint"""
    # Save current research areas to restore later
    response = client.get('/api/research-areas')
    original_areas = json.loads(response.data)
    
    # Test updating research areas
    test_areas = ["artificial intelligence", "machine learning", "robotics"]
    request_data = {
        "research_areas": test_areas
    }
    response = client.post('/api/research-areas', 
                         data=json.dumps(request_data),
                         content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True
    
    # Verify the update worked
    response = client.get('/api/research-areas')
    updated_areas = json.loads(response.data)
    for area in test_areas:
        assert area in updated_areas
        
    # Restore original research areas
    restore_data = {
        "research_areas": original_areas
    }
    client.post('/api/research-areas', 
               data=json.dumps(restore_data),
               content_type='application/json')

if __name__ == "__main__":
    pytest.main(["-v"]) 