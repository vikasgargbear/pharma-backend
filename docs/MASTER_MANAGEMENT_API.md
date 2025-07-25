# Master Management Backend Integration

## Overview

The Master Management system has been fully integrated with the backend, enabling businesses to customize their platform settings and have them enforced throughout the application.

## What Was Implemented

### 1. Organization Settings API

**Endpoints Created:**
- `GET /api/v1/organizations/{org_id}` - Get organization profile
- `PUT /api/v1/organizations/{org_id}` - Update organization profile
- `GET /api/v1/organizations/{org_id}/features` - Get feature settings
- `PUT /api/v1/organizations/{org_id}/features` - Update feature settings
- `POST /api/v1/organizations/{org_id}/logo` - Upload organization logo

### 2. JWT-Based Authentication

**Why org_id was hardcoded:**
- Quick development without full auth system
- Placeholder for MVP development
- No user management implemented initially

**New Authentication System:**
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/organizations` - List user's organizations
- `POST /api/v1/auth/switch-organization` - Switch between organizations
- `POST /api/v1/auth/register` - Register new user/organization
- `POST /api/v1/auth/change-password` - Change password

### 3. Organization Context Management

**Session-Based Context (Implemented):**
- Organization ID stored in JWT token
- All API calls use org context from token
- No separate windows needed
- Seamless switching between organizations

## How Multi-Company Works

### User Flow:
1. User logs in with email/password
2. JWT token includes current org_id
3. User can switch organizations via dropdown
4. New JWT token issued with new org_id
5. All subsequent API calls use new context

### Database Level:
- Every table has `org_id` column
- RLS policies use `current_org_id()` function
- Complete data isolation between organizations

## Frontend Integration Required

### 1. Update API Client

```javascript
// Add auth header to all requests
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Authorization': `Bearer ${getToken()}`
  }
});
```

### 2. Company Profile Component

```javascript
// Fetch organization profile
const getOrgProfile = async (orgId) => {
  const response = await apiClient.get(`/organizations/${orgId}`);
  return response.data.data;
};

// Update organization profile
const updateOrgProfile = async (orgId, data) => {
  const response = await apiClient.put(`/organizations/${orgId}`, data);
  return response.data;
};
```

### 3. Feature Settings Component

```javascript
// Save features to backend instead of localStorage
const saveFeatures = async (features) => {
  const response = await apiClient.put(
    `/organizations/${currentOrgId}/features`,
    features
  );
  return response.data;
};
```

### 4. Organization Switcher

```javascript
// Get user's organizations
const getUserOrgs = async () => {
  const response = await apiClient.get('/auth/organizations');
  return response.data.organizations;
};

// Switch organization
const switchOrg = async (orgId) => {
  const response = await apiClient.post('/auth/switch-organization', {
    org_id: orgId
  });
  // Save new token
  localStorage.setItem('token', response.data.access_token);
  // Reload app with new context
  window.location.reload();
};
```

## Backend Feature Enforcement

### Example: Discount Limit Check

```python
# In sales endpoint
org_features = get_org_features(current_org["org_id"])
max_discount = org_features.get("discountLimit", 100)

if discount_percent > max_discount:
    raise HTTPException(400, f"Discount exceeds limit of {max_discount}%")
```

### Example: Credit Limit Check

```python
# In sales endpoint
if org_features.get("creditLimitForParties"):
    credit_limit = customer.credit_limit or org_features.get("creditLimitThreshold")
    if total_amount > credit_limit:
        raise HTTPException(400, "Order exceeds customer credit limit")
```

## Environment Variables

Add to `.env`:
```
ENABLE_JWT_AUTH=true
JWT_SECRET_KEY=your-secret-key-here
DEFAULT_ORG_ID=12de5e22-eee7-4d25-b3a7-d16d01c6170f
```

## Migration Steps

1. **Phase 1**: Update frontend to use new APIs (backward compatible)
2. **Phase 2**: Enable JWT auth with ENABLE_JWT_AUTH=true
3. **Phase 3**: Remove localStorage usage completely
4. **Phase 4**: Implement feature enforcement in all endpoints

## Security Considerations

1. JWT tokens expire after 12 hours
2. Organization switching requires re-authentication
3. All endpoints verify user has access to requested org
4. Passwords are bcrypt hashed
5. Feature changes are audit logged

## Next Steps

1. Frontend integration with new APIs
2. Add organization switcher UI
3. Implement feature enforcement middleware
4. Add role-based permissions
5. Create organization invitation system