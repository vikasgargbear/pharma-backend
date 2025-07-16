# Enterprise API Test Suite

## Overview

This is a comprehensive, production-ready test suite for the Pharmaceutical Management System APIs. The suite includes over 200 tests covering authentication, business logic, financial operations, integrations, security, and performance.

## Test Categories

### 1. **Authentication Tests** (`test_authentication.py`)
- User registration and login
- JWT token validation and refresh
- Role-based access control (RBAC)
- Password management
- Session management
- Brute force protection
- SQL injection in auth endpoints

### 2. **Core Business Tests** (`test_core_business.py`)
- Product management (CRUD, search, validation)
- Customer management
- Order processing workflow
- Inventory and batch management
- Drug schedule compliance
- Business rule validation

### 3. **Financial Tests** (`test_financial.py`)
- Payment recording and reconciliation
- Invoice generation with GST calculations
- Credit note generation
- Customer credit management
- Outstanding aging reports
- Payment reminders

### 4. **Integration Tests** (`test_integration.py`)
- WhatsApp messaging
- SMS notifications and OTP
- Email notifications
- File uploads (images, PDFs)
- External API integrations (GST verification, pincode lookup)

### 5. **Security Tests** (`test_security.py`)
- SQL injection vulnerabilities
- Cross-site scripting (XSS)
- Authentication bypass attempts
- CSRF protection
- Rate limiting
- Sensitive data exposure
- File upload security

### 6. **Performance Tests** (`test_performance.py`)
- Endpoint response times
- Concurrent load handling
- Stress testing
- Database query performance
- Bulk operation performance
- Sustained load testing

## Quick Start

### Prerequisites
```bash
pip install pytest pytest-json-report pytest-parallel requests
```

### Run All Tests
```bash
# Run complete test suite
python tests/run_enterprise_tests.py

# Run with specific environment
python tests/run_enterprise_tests.py --env staging

# Run specific category
python tests/run_enterprise_tests.py --category security

# Run quick smoke tests
python tests/run_enterprise_tests.py --quick
```

### Run Individual Test Modules
```bash
# Run authentication tests
pytest tests/test_authentication.py -v

# Run specific test
pytest tests/test_authentication.py::TestAuthentication::test_login_valid_credentials -v

# Run with markers
pytest tests/test_core_business.py -m "not slow" -v
```

## Configuration

### Environment Setup
Create a `.env` file in the tests directory:
```env
# Test Environment
TEST_ENV=local

# API Configuration
LOCAL_API_URL=http://localhost:8000
STAGING_API_URL=https://staging-api.pharmaco.com
PROD_API_URL=https://api.pharmaco.com

# Test User Credentials
TEST_ADMIN_USER=admin@pharmaco.com
TEST_ADMIN_PASS=AdminTest123!

# Performance Thresholds
PERF_THRESHOLD_AUTH=1.0
PERF_THRESHOLD_READ=0.5
PERF_THRESHOLD_WRITE=1.0
```

### Test Data Factory
The suite includes a comprehensive test data factory that generates:
- Valid GST numbers
- Indian phone numbers
- Product data with proper HSN codes
- Customer data with credit limits
- Order data with multiple items
- Batch data with expiry tracking

## Test Reports

After running tests, the following reports are generated in `test_results/`:

1. **HTML Report** (`test_report.html`)
   - Visual summary with charts
   - Category-wise breakdown
   - Pass/fail rates

2. **JSON Summary** (`test_summary.json`)
   - Machine-readable results
   - Detailed metrics
   - Performance data

3. **JUnit XML** (`*.xml`)
   - CI/CD integration
   - Jenkins/GitLab compatible

4. **Test Metrics** (`test_metrics.json`)
   - Performance percentiles
   - Slowest tests
   - Error logs

## CI/CD Integration

### GitHub Actions
```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      
      - name: Run tests
        run: python tests/run_enterprise_tests.py --env staging
      
      - name: Upload test results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-results
          path: test_results/
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                sh 'python tests/run_enterprise_tests.py --env ${TEST_ENV}'
            }
            post {
                always {
                    junit 'test_results/*.xml'
                    publishHTML target: [
                        reportDir: 'test_results',
                        reportFiles: 'test_report.html',
                        reportName: 'API Test Report'
                    ]
                }
            }
        }
    }
}
```

## Performance Benchmarks

The suite enforces the following performance benchmarks:

| Operation Type | Target (avg) | Target (p95) |
|----------------|--------------|--------------|
| Authentication | < 1.0s       | < 2.0s       |
| Read (single)  | < 0.5s       | < 1.0s       |
| Read (list)    | < 0.5s       | < 1.5s       |
| Create         | < 1.0s       | < 2.0s       |
| Update         | < 1.0s       | < 2.0s       |
| Complex Query  | < 2.0s       | < 5.0s       |

## Security Testing

The security tests check for:
- OWASP Top 10 vulnerabilities
- Authentication bypasses
- Injection attacks (SQL, NoSQL, Command)
- XSS in all input fields
- CSRF token validation
- Rate limiting effectiveness
- Sensitive data exposure
- File upload vulnerabilities

## Best Practices

1. **Test Isolation**: Each test is independent and cleans up after itself
2. **Test Data**: Use the TestDataFactory for consistent test data
3. **Parallel Execution**: Tests can run in parallel for faster execution
4. **Environment Agnostic**: Tests work across local, staging, and production
5. **Comprehensive Coverage**: Every API endpoint has multiple test scenarios
6. **Performance Tracking**: All tests measure and report response times

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure the API server is running
   - Check the API URL in configuration

2. **Authentication Failures**
   - Verify test user credentials
   - Check if test users exist in the database

3. **Timeout Errors**
   - Increase timeout values for slow environments
   - Check network connectivity

4. **Test Data Conflicts**
   - Run cleanup script: `python tests/cleanup_test_data.py`
   - Use unique identifiers in test data

## Extending the Test Suite

### Adding New Tests
1. Create test file following naming convention: `test_*.py`
2. Inherit from `APITestBase` for common functionality
3. Use fixtures for setup/teardown
4. Register test data for automatic cleanup

### Adding New Categories
1. Update `TEST_CATEGORIES` in `test_suite_config.py`
2. Create corresponding test module
3. Update the test runner to recognize the category

## Maintenance

### Regular Tasks
- Review and update performance thresholds quarterly
- Add tests for new API endpoints
- Update security tests for new vulnerabilities
- Maintain test data factories for new fields

### Test Health Metrics
- Aim for >95% pass rate
- Keep test execution under 10 minutes
- Maintain <5% flaky test rate
- Ensure 100% endpoint coverage