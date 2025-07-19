# Scripts Directory

Organized utility scripts for the pharma-backend project.

## Directory Structure

### `/deployment`
Scripts for deploying the application:
- `start_app.py` - Start the FastAPI application
- `start_production.py` - Start with production settings
- `start_server.py` - Basic server startup

### `/migration`
Database migration scripts:
- `run_migrations.py` - Run all pending migrations
- `run_order_migrations.py` - Run order-specific migrations
- `fix_imports.py` - Fix import issues

### `/testing`
Test execution scripts:
- `run_tests.py` - Main test runner
- `test_*.py` - Various endpoint test scripts
- `demonstrate_test_suite.py` - Demo of test capabilities

### `/demo`
Demo and sample data:
- `demo_script.py` - Interactive demo script
- `test_*.json` - Sample JSON payloads for testing

## Usage Examples

```bash
# Run the application
python scripts/deployment/start_app.py

# Run migrations
python scripts/migration/run_migrations.py

# Run tests
python scripts/testing/run_tests.py

# Run demo
python scripts/demo/demo_script.py
```