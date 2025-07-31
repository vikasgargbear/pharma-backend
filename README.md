# AASO Pharma ERP - Backend API

## Overview
FastAPI-based backend service for pharmaceutical ERP system with comprehensive inventory management, sales processing, GST compliance, and financial operations.

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (Supabase)
- Git

### Installation
```bash
# Clone repository
git clone [repository-url]
cd pharma-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Update .env with your configuration

# Run development server
uvicorn api.main:app --reload --port 8000
```

### Environment Configuration
Create `.env` file with:
```env
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key

# Authentication
JWT_SECRET_KEY=your_jwt_secret
JWT_ALGORITHM=HS256

# Environment
ENVIRONMENT=development
DEBUG=true
```

## Project Structure
```
pharma-backend/
├── api/                    # Main application
│   ├── routers/           # API endpoints
│   ├── models/            # Database models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   ├── utils/             # Utilities
│   └── main.py            # FastAPI app
├── database/              # Database management
│   ├── migrations/        # Alembic migrations
│   └── supabase/         # Supabase setup
├── tests/                 # Test suite
├── scripts/               # Utility scripts
└── docs/                  # Documentation
```

## Key Features
- 📦 **Inventory Management** - Real-time stock tracking with batch/expiry
- 💰 **Sales Processing** - Invoice generation with GST compliance
- 🛒 **Purchase Management** - PO, GRN, and vendor management
- 🔄 **Returns Processing** - Credit/debit notes with GST handling
- 📊 **Financial Reports** - P&L, aging, GST returns
- 🏦 **Payment Processing** - Multiple payment modes and tracking
- 👥 **Multi-tenant** - Organization-based data isolation
- 🔐 **Security** - JWT authentication with role-based access

## API Endpoints Overview

### Core Modules
- `/api/products` - Product management and search
- `/api/customers` - Customer management and search
- `/api/sales` - Invoice creation and management
- `/api/purchases` - Purchase orders and receipts
- `/api/inventory` - Stock management and adjustments
- `/api/returns` - Sales and purchase returns
- `/api/reports` - Analytics and reporting
- `/api/payments` - Payment processing and tracking

### System Endpoints
- `/api/health` - Health check
- `/api/docs` - Interactive API documentation
- `/api/database-tools` - Database inspection and management

## Technology Stack
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT with Supabase Auth
- **Validation**: Pydantic 2.0
- **Migration**: Alembic
- **Deployment**: Railway
- **Documentation**: OpenAPI/Swagger

## Current Status
- ✅ **API Deployed**: https://pharma-backend-production-0c09.up.railway.app
- ✅ **Core Modules**: Sales, Purchase, Inventory operational
- ✅ **Database**: PostgreSQL with RLS policies
- ✅ **Authentication**: JWT-based auth system
- 🚧 **Schema Alignment**: Some model-database mismatches
- 🚧 **Advanced Features**: Reports and analytics in progress

## Recent Updates
- Fixed schema mismatches and import issues
- Added database inspection tools
- Optimized query performance
- Enhanced error handling
- Added comprehensive logging

## Development Commands
```bash
# Start development server
uvicorn api.main:app --reload

# Run tests
pytest

# Generate migrations
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Database inspection
python -c "from api.utils.db_inspector import inspect_all; inspect_all()"
```

## Deployment
- **Production**: Deployed on Railway
- **Database**: Hosted on Supabase
- **Auto-deploy**: Connected to GitHub main branch
- **Health Check**: Available at `/api/health`

## Documentation
- [API Reference](./API_REFERENCE.md) - Complete API documentation
- [Database Guide](./DATABASE.md) - Schema and management
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment
- [Development Guide](./DEVELOPMENT.md) - Local development
- [Architecture Overview](./ARCHITECTURE.md) - System design

## Support
- **API Documentation**: `/api/docs` (Swagger UI)
- **Health Status**: `/api/health`
- **Database Tools**: `/api/database-tools`

For issues or questions, refer to the documentation or contact the development team.