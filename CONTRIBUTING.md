# Contributing to Pharma ERP Backend

Thank you for your interest in contributing to our Enterprise Pharmaceutical ERP Backend!

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/pharma-erp-backend.git
   cd pharma-erp-backend
   ```

3. Set up local PostgreSQL or Supabase project for development
4. Run the test suite to ensure everything works

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our conventions
3. Test your changes:
   ```sql
   SELECT * FROM testing.run_all_tests();
   ```

4. Commit with conventional commits:
   ```bash
   git commit -m "feat: add new GST report generation"
   git commit -m "fix: correct inventory allocation logic"
   git commit -m "docs: update API documentation"
   ```

5. Push and create a pull request

## Database Development Guidelines

### Schema Changes
- Always add new columns as nullable first
- Provide migration scripts for schema changes
- Update relevant triggers and functions
- Add/update indexes for new queries

### API Development
- Follow existing API naming conventions
- Always return JSONB
- Include proper error handling
- Document parameters and return structure
- Add tests for new APIs

### SQL Style Guide
```sql
-- Use lowercase for keywords
CREATE OR REPLACE FUNCTION api.function_name(
    p_param1 INTEGER,
    p_param2 TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- Function logic here
    RETURN v_result;
END;
$$;
```

### Naming Conventions
- Tables: `snake_case` (e.g., `invoice_items`)
- Columns: `snake_case` (e.g., `customer_id`)
- Functions: `snake_case` (e.g., `calculate_gst_amount`)
- Triggers: `trg_[table]_[action]` (e.g., `trg_invoices_before_insert`)
- Indexes: `idx_[table]_[columns]` (e.g., `idx_invoices_customer_date`)

## Testing

All changes must include tests:

```sql
-- Add test to testing suite
CREATE OR REPLACE FUNCTION testing.test_your_feature()
RETURNS VOID AS $$
BEGIN
    -- Test logic
    PERFORM testing.assert_equals(expected, actual, 'Test description');
END;
$$ LANGUAGE plpgsql;
```

## Documentation

- Update API documentation for new endpoints
- Add inline comments for complex logic
- Update README if adding new features
- Document any breaking changes

## Pull Request Process

1. Ensure all tests pass
2. Update documentation
3. Fill out the PR template completely
4. Wait for code review
5. Address review comments
6. Merge after approval

## Commit Message Format

We use conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Test additions/changes
- `chore:` Maintenance tasks

## Questions?

Feel free to open an issue for any questions about contributing.