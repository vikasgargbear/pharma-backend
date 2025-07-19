# Enterprise Project Structure

## Proposed Directory Organization

```
pharma-backend/
├── api/                    # Core API application (existing)
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   └── schemas_v2/        # Pydantic schemas
│
├── database/              # Database related (existing)
│   ├── migrations/        # Version control for DB
│   └── supabase/         # Supabase specific scripts
│
├── tests/                 # All test files (existing)
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── e2e/              # End-to-end tests
│
├── scripts/               # Utility scripts (NEW)
│   ├── deployment/       # Deployment scripts
│   ├── migration/        # Database migration scripts
│   ├── testing/          # Test runner scripts
│   └── demo/             # Demo and sample scripts
│
├── docs/                  # Documentation (NEW)
│   ├── api/              # API documentation
│   ├── deployment/       # Deployment guides
│   ├── development/      # Development guides
│   └── architecture/     # System architecture docs
│
├── config/                # Configuration files (NEW)
│   ├── development/      # Dev environment config
│   ├── production/       # Prod environment config
│   └── testing/          # Test environment config
│
├── .github/               # GitHub specific
│   └── workflows/        # CI/CD workflows
│
├── requirements/          # Dependencies (NEW)
│   ├── base.txt         # Base requirements
│   ├── development.txt  # Dev requirements
│   └── production.txt   # Prod requirements
│
└── Root files (keep minimal):
    ├── README.md
    ├── .env.example
    ├── .gitignore
    ├── main.py
    ├── railway.json
    ├── vercel.json
    └── requirements.txt
```

## Files to Move

### To `scripts/deployment/`:
- start_app.py
- start_production.py
- start_server.py
- DEPLOY_RAILWAY.md → docs/deployment/
- RAILWAY_DEPLOYMENT_GUIDE.md → docs/deployment/

### To `scripts/migration/`:
- run_migrations.py
- run_order_migrations.py
- fix_imports.py

### To `scripts/testing/`:
- run_tests.py
- test_critical_endpoints.py
- test_endpoints.py
- test_order_endpoints.py
- test_inventory_prod.py
- test_inventory_local.py
- test_customer_endpoints.py
- test_simple_customers.py
- demonstrate_test_suite.py

### To `scripts/demo/`:
- demo_script.py
- test_batch.json
- test_order.json
- test_invoice.json

### To `docs/api/`:
- API_WORKING_SUMMARY.md
- ENDPOINT_STATUS.md
- DATA_DICTIONARY.md

### To `docs/deployment/`:
- DEPLOYMENT_*.md files
- DEPLOY_INSTRUCTIONS.md
- GITHUB_*.md files
- RAILWAY_*.md files

### To `docs/development/`:
- BACKEND_IMPLEMENTATION_GUIDE.md
- ENTERPRISE_PHARMA_*.md
- HOW_COMPANIES_SCALE.md
- SCALING_LESSONS.md

### To `docs/architecture/`:
- COMPONENT_DEPENDENCY_VISUALIZATION.md
- SYSTEM_DEPENDENCY_MAP.md
- DEPENDENCY_ANALYSIS_*.md/json
- ALL_FUNCTIONS_DETAILED.md
- COMPLETE_FUNCTION_MAPPING.md

### To `docs/project-status/`:
- CURRENT_STATE.md
- PROGRESS_UPDATE.md
- SUCCESS_REPORT.md
- FINAL_*.md files
- CLEANUP_*.md files
- ORDER_*.md files