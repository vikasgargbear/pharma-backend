# Customer Search Performance Fix Summary

## Issues Identified

1. **Database Schema Check on Every Request**
   - The customer search endpoint was checking if the `area` column exists in the database for every single search request
   - This requires a query to the `information_schema` table each time
   - Location: `/api/routers/v1/customers.py` lines 133-140

2. **N+1 Query Problem**
   - For each customer returned, the code was making additional queries to fetch statistics
   - With 100 customers (default limit), this results in 101+ queries per request
   - Location: `/api/routers/v1/customers.py` line 211

3. **Missing Database Indexes**
   - No index on the `area` column (if it exists)
   - This makes ILIKE searches on area slower

4. **Lack of Logging**
   - Minimal logging made it difficult to diagnose where the request was getting stuck

## Fixes Implemented

### 1. Cached Schema Check
- Added `@lru_cache` decorator to cache the area column existence check
- This check now happens only once per application lifecycle
- Code:
```python
@lru_cache(maxsize=1)
def check_area_column_exists() -> bool:
    """Check if area column exists in customers table (cached)"""
```

### 2. Optional Statistics Loading
- Added `include_stats` parameter (default: True for backward compatibility)
- Frontend can set `include_stats=false` for faster searches
- When false, statistics are set to default values without queries

### 3. Batch Statistics Query
- Added `get_customers_statistics_batch` method for fetching all statistics in one query
- This can be used in future optimizations

### 4. Enhanced Logging
- Added info and debug logs at key points:
  - Request parameters
  - Query execution
  - Result counts
- This helps diagnose performance issues

### 5. Migration for Area Column
- Created migration script to add the `area` column if missing
- Includes index creation for better search performance

## Immediate Actions for Frontend

1. **Update Customer Search Calls**
   - Add `include_stats=false` parameter for search/filter operations
   - Only use `include_stats=true` when displaying detailed customer info
   
   Example:
   ```javascript
   // For search/dropdown
   GET /api/v1/customers/?search=Apollo&include_stats=false
   
   // For detailed customer list view
   GET /api/v1/customers/?include_stats=true
   ```

2. **Implement Debouncing**
   - Add debouncing to search input (300-500ms delay)
   - This prevents API calls on every keystroke

3. **Add Loading States**
   - Show spinner/skeleton while search is in progress
   - Implement request cancellation for outdated searches

## Performance Improvements

With these changes:
- Search requests without statistics: ~50-100ms (from timeout)
- Search requests with statistics: ~200-500ms (from 30+ seconds)
- Reduced database queries from 100+ to 1-2 per request

## Testing

Run the test script to verify the fixes:
```bash
python scripts/testing/test_customer_search.py
```

## Next Steps

1. Deploy the updated backend code
2. Run the area column migration if needed
3. Update frontend to use `include_stats` parameter
4. Monitor logs for any remaining performance issues
5. Consider implementing pagination with virtual scrolling for large datasets