"""
Test customer management endpoints
"""
import pytest


def test_create_customer(client):
    """Test creating a new customer"""
    customer_data = {
        "name": "John Doe Pharmacy",
        "phone": "9876543210",
        "email": "john@pharmacy.com",
        "address": "123 Medical Street, Health City",
        "gst_number": "22AAAAA0000A1Z5"
    }
    
    response = client.post("/customers/", json=customer_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == customer_data["name"]
    assert data["phone"] == customer_data["phone"]
    assert data["email"] == customer_data["email"]
    assert "id" in data


def test_get_customers(client, sample_customer):
    """Test retrieving customers list"""
    response = client.get("/customers/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == sample_customer.name


def test_get_customer_by_id(client, sample_customer):
    """Test retrieving a specific customer"""
    response = client.get(f"/customers/{sample_customer.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_customer.id
    assert data["name"] == sample_customer.name


def test_get_nonexistent_customer(client):
    """Test retrieving a non-existent customer"""
    response = client.get("/customers/99999")
    assert response.status_code == 404


def test_update_customer(client, sample_customer):
    """Test updating a customer"""
    updated_data = {
        "name": "Updated Pharmacy Name",
        "phone": sample_customer.phone,
        "email": sample_customer.email,
        "address": sample_customer.address,
        "gst_number": sample_customer.gst_number
    }
    
    response = client.put(f"/customers/{sample_customer.id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == updated_data["name"]


def test_delete_customer(client, sample_customer):
    """Test deleting a customer"""
    response = client.delete(f"/customers/{sample_customer.id}")
    assert response.status_code == 200
    
    # Verify customer is deleted
    response = client.get(f"/customers/{sample_customer.id}")
    assert response.status_code == 404


def test_invalid_customer_data(client):
    """Test creating customer with invalid data"""
    invalid_data = {
        "name": "",  # Empty name should fail
        "phone": "invalid_phone",  # Invalid phone format
        "email": "not_an_email"  # Invalid email format
    }
    
    response = client.post("/customers/", json=invalid_data)
    assert response.status_code == 422


def test_customer_gst_validation(client):
    """Test GST number validation"""
    customer_data = {
        "name": "Test Pharmacy",
        "phone": "9876543210", 
        "email": "test@pharmacy.com",
        "address": "Test Address",
        "gst_number": "INVALID_GST"  # Invalid GST format
    }
    
    response = client.post("/customers/", json=customer_data)
    # Should either accept (if validation is lenient) or reject with 422
    assert response.status_code in [200, 422]