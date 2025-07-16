"""
Test configuration and fixtures for the Pharma ERP system
"""
import pytest
import tempfile
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.database import get_db, Base
from api.models import User, Customer, Product, Batch


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    },
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """Create a test client with dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_customer(db_session):
    """Create a sample customer for testing"""
    customer = Customer(
        name="Test Customer",
        phone="9876543210",
        email="customer@test.com",
        address="123 Test Street",
        gst_number="22AAAAA0000A1Z5"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def sample_product(db_session):
    """Create a sample product for testing"""
    product = Product(
        name="Test Medicine",
        brand_name="TestBrand",
        manufacturer="Test Pharma Ltd",
        drug_schedule="H",
        unit_type="Strip",
        mrp=100.0,
        purchase_rate=80.0,
        gst_percentage=12.0,
        hsn_code="30049099"
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture
def sample_batch(db_session, sample_product):
    """Create a sample batch for testing"""
    batch = Batch(
        product_id=sample_product.id,
        batch_number="TEST001",
        quantity=100,
        expiry_date="2025-12-31",
        purchase_rate=80.0,
        mrp=100.0
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture
def auth_headers(client, sample_user):
    """Get authentication headers for API testing"""
    # Login to get token
    response = client.post(
        "/auth/login",
        data={"username": sample_user.username, "password": "secret"}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}