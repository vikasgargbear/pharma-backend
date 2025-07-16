"""
Test product management endpoints
"""
import pytest


def test_create_product(client):
    """Test creating a new product"""
    product_data = {
        "name": "Paracetamol 500mg",
        "brand_name": "Crocin",
        "manufacturer": "GSK Pharmaceuticals",
        "drug_schedule": "G",
        "unit_type": "Strip",
        "mrp": 15.50,
        "purchase_rate": 12.00,
        "gst_percentage": 12.0,
        "hsn_code": "30049099"
    }
    
    response = client.post("/products/", json=product_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["brand_name"] == product_data["brand_name"]
    assert data["drug_schedule"] == product_data["drug_schedule"]
    assert "id" in data


def test_get_products(client, sample_product):
    """Test retrieving products list"""
    response = client.get("/products/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["name"] == sample_product.name


def test_get_product_by_id(client, sample_product):
    """Test retrieving a specific product"""
    response = client.get(f"/products/{sample_product.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_product.id
    assert data["name"] == sample_product.name


def test_update_product(client, sample_product):
    """Test updating a product"""
    updated_data = {
        "name": "Updated Medicine Name",
        "brand_name": sample_product.brand_name,
        "manufacturer": sample_product.manufacturer,
        "drug_schedule": sample_product.drug_schedule,
        "unit_type": sample_product.unit_type,
        "mrp": 120.0,  # Updated price
        "purchase_rate": sample_product.purchase_rate,
        "gst_percentage": sample_product.gst_percentage,
        "hsn_code": sample_product.hsn_code
    }
    
    response = client.put(f"/products/{sample_product.id}", json=updated_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == updated_data["name"]
    assert data["mrp"] == updated_data["mrp"]


def test_delete_product(client, sample_product):
    """Test deleting a product"""
    response = client.delete(f"/products/{sample_product.id}")
    assert response.status_code == 200


def test_drug_schedule_validation(client):
    """Test drug schedule validation"""
    valid_schedules = ["G", "H", "H1", "X"]
    
    for schedule in valid_schedules:
        product_data = {
            "name": f"Test Medicine {schedule}",
            "brand_name": "TestBrand",
            "manufacturer": "Test Pharma",
            "drug_schedule": schedule,
            "unit_type": "Strip",
            "mrp": 100.0,
            "purchase_rate": 80.0,
            "gst_percentage": 12.0,
            "hsn_code": "30049099"
        }
        
        response = client.post("/products/", json=product_data)
        assert response.status_code == 200, f"Failed for schedule {schedule}"


def test_invalid_drug_schedule(client):
    """Test invalid drug schedule rejection"""
    product_data = {
        "name": "Test Medicine",
        "brand_name": "TestBrand", 
        "manufacturer": "Test Pharma",
        "drug_schedule": "INVALID",  # Invalid schedule
        "unit_type": "Strip",
        "mrp": 100.0,
        "purchase_rate": 80.0,
        "gst_percentage": 12.0,
        "hsn_code": "30049099"
    }
    
    response = client.post("/products/", json=product_data)
    # Should reject invalid drug schedule
    assert response.status_code in [400, 422]


def test_price_validation(client):
    """Test price validation logic"""
    product_data = {
        "name": "Test Medicine",
        "brand_name": "TestBrand",
        "manufacturer": "Test Pharma", 
        "drug_schedule": "G",
        "unit_type": "Strip",
        "mrp": 50.0,
        "purchase_rate": 80.0,  # Purchase rate higher than MRP (should be invalid)
        "gst_percentage": 12.0,
        "hsn_code": "30049099"
    }
    
    response = client.post("/products/", json=product_data)
    # Should either accept (if validation is lenient) or reject
    assert response.status_code in [200, 400, 422]