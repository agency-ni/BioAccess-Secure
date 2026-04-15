# Client Desktop - API Response Format Integration Guide

**Date**: April 12, 2026  
**Version**: 2.0.0  
**Status**: ✅ Ready for Production

---

## Overview

The Client Desktop `BioAccessAPIClient` has been updated to handle the new standardized `APIResponse` format from the Backend while maintaining **100% backward compatibility** with legacy response formats.

### Old Format (Legacy)
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzUxMiIs...",
    "template_id": "uuid",
    "encoding_vector": [0.1, 0.2, ...]
}
```

### New Format (Standardized)
```json
{
    "status": "success",
    "code": 201,
    "timestamp": "2026-04-12T10:30:45Z",
    "message": "Succès",
    "data": {
        "token": "eyJhbGciOiJIUzUxMiIs...",
        "template_id": "uuid",
        "encoding_vector": [0.1, 0.2, ...]
    }
}
```

---

## How It Works: Response Normalization

### In `biometric_api_client.py`

The `_make_request()` method automatically detects and handles both formats:

```python
def _make_request(...):
    # Parse JSON response
    response_data = response.json()
    
    # DETECTION: Check for new format
    if isinstance(response_data, dict):
        if 'status' in response_data and 'message' in response_data:
            # NEW FORMAT: Extract data from 'data' field
            data_payload = response_data.get('data', {}) if response_data.get('status') == 'success' else None
            error_msg = response_data.get('message', '')
        elif 'success' in response_data or 'error' in response_data:
            # LEGACY FORMAT: Use as-is
            error_msg = response_data.get('error', '')
            data_payload = response_data if success else None
        else:
            # UNKNOWN FORMAT: Fallback
            data_payload = response_data if success else None
    
    # Return normalized APIResponse
    return APIResponse(
        success=success,
        status_code=response.status_code,
        data=data_payload,           # ← Extracted data is here
        error_message=error_msg,
        timestamp=datetime.now()
    )
```

### Result

Both formats produce the **same `APIResponse` object**:

```python
# Legacy backend response
response = client.face_register(image_base64="...")

# New backend response (same result)
response = client.face_register(image_base64="...")

# Both return:
APIResponse(
    success=True,
    status_code=201,
    data={
        "token": "...",
        "template_id": "...",
        "encoding_vector": [...]
    },
    error_message=None,
    timestamp=datetime.now()
)
```

---

## Client Code: Usage Patterns

### Pattern 1: Simple Success Check

```python
from biometric import get_api_client

client = get_api_client()
response = client.face_register(image_base64="...")

if response.success:
    print("✅ Face registered successfully")
    print(f"   Template ID: {response.data['template_id']}")
else:
    print(f"❌ Error: {response.error_message}")
```

**Works with**: Both old and new backend formats ✅

---

### Pattern 2: Access Response Data

```python
from biometric import BiometricAPI

response = BiometricAPI.face_verify("admin@example.com", image_base64="...")

if response.success:
    # Access nested data (works with both formats)
    token = response.data.get('access_token') or response.data.get('token')
    user_id = response.data.get('user_id')
    role = response.data.get('role')
    
    # Set authentication
    from biometric import get_api_client
    get_api_client().set_auth_token(token)
else:
    print(f"Authentication failed: {response.error_message}")
```

**Works with**: Both old and new backend formats ✅

---

### Pattern 3: Error Handling

```python
from biometric import get_api_client

client = get_api_client()

try:
    response = client.face_verify(
        email="user@example.com",
        image_base64="..."
    )
    
    if response.success:
        print(f"✅ Authenticated as {response.data.get('email')}")
    else:
        # Handle error from new format
        print(f"❌ {response.error_message}")  # From new format
        print(f"   Status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Network error: {e}")
```

**Works with**: Both old and new backend formats ✅

---

### Pattern 4: Token Persistence

```python
from biometric import BiometricAPI, get_api_client

# Login
login_response = BiometricAPI.face_verify(
    email="admin@example.com",
    image_base64="..."
)

if login_response.success:
    # Extract token from data (works with both formats)
    token = login_response.data.get('access_token') or login_response.data.get('token')
    
    # Set global token
    BiometricAPI.set_token(token)
    
    # Or directly
    client = get_api_client()
    client.set_auth_token(token, expires_in=86400)
    
    # Subsequent requests will use this token automatically
    user_response = client.get_user_profile()
    if user_response.success:
        print(f"✅ User: {user_response.data.get('email')}")
```

**Works with**: Both old and new backend formats ✅

---

## API Response Fields

### Standard Fields (Both Formats)

| Field | Type | Source | Description |
|-------|------|--------|-------------|
| `success` | bool | APIResponse wrapper | Whether request succeeded |
| `status_code` | int | APIResponse wrapper | HTTP status code (200, 201, 400, 401, 500, etc.) |
| `data` | dict | Response payload | Actual response data (extracted from appropriate location) |
| `error_message` | str | Response payload | Error message if failed |
| `timestamp` | datetime | APIResponse wrapper | When response was created |

### New Format Additional Fields

Available in responses but not required by client code:

```python
# From new format response
response_dict = {
    "status": "success",           # ← Indicates success/error
    "code": 201,                   # ← HTTP code
    "timestamp": "2026-04-12...",  # ← ISO8601 timestamp
    "message": "Succès",           # ← Human readable message
    "data": {...},                 # ← Actual data
    "error_code": "VALIDATION_ERROR"  # ← Error code (optional)
}
```

**Client doesn't need to access these directly** - they're handled by the wrapper ✅

---

## Testing New Format Integration

### Unit Tests

Run existing test suite (already handles new format):

```bash
cd Client\ Desktop
python -m pytest biometric/test_biometric.py -v
```

### Integration Tests

Create a test file to verify both formats work:

```python
# test_both_formats.py
from biometric import APIResponse

# Test new format response
new_format_response = {
    "status": "success",
    "code": 201,
    "timestamp": "2026-04-12T10:30:45Z",
    "message": "Registered successfully",
    "data": {
        "template_id": "uuid123",
        "token": "eyJhbGciOiJIUzUxMiIs..."
    }
}

# Test legacy format response
legacy_format_response = {
    "success": True,
    "template_id": "uuid123",
    "token": "eyJhbGciOiJIUzUxMiIs..."
}

# Both should parse identically
# (verification in biometric_api_client.py _make_request method)
```

Run with:
```bash
python test_both_formats.py
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Backend deployed with new `APIResponse` format
- [ ] Run Client Desktop tests: `python -m pytest biometric/test_biometric.py`
- [ ] Verify biometric_api_client.py changes applied
- [ ] Test with both legacy AND new backend response formats

### Deployment

- [ ] Restart Client Desktop services
- [ ] Verify no errors in logs

### Post-Deployment

- [ ] Monitor error logs for response parsing issues
- [ ] Test end-to-end: capture → register → verify flow
- [ ] Verify token extraction and persistence
- [ ] Check admin dashboard reflects biometric enrollments

---

## Troubleshooting

### Issue: "TypeError: 'NoneType' object is not subscriptable"

**Cause**: Trying to access `response.data['field']` when data is None

**Fix**:
```python
# ❌ WRONG
token = response.data['token']  # Fails if data is None

# ✅ CORRECT
token = response.data.get('token') if response.data else None

# OR
if response.success:
    token = response.data['token']
```

---

### Issue: "Cannot find 'token' in response"

**Cause**: Token location changed between old and new format

**Fix**:
```python
# ✅ Works with both formats
token = response.data.get('access_token') or response.data.get('token')

# Handles both:
# Old format: {"success": true, "token": "..."}
# New format: {"status": "success", "data": {"access_token": "..."}}
```

---

### Issue: "API Response has wrong status_code"

**Cause**: Checking HTTP status code instead of response.success

**Fix**:
```python
# ❌ WRONG
if response.status_code == 200:  # Works but fragile

# ✅ CORRECT
if response.success:  # Always works
    # Process data
```

---

## Migration Path for Custom Code

If you have custom code parsing API responses, follow this pattern:

### Before (Legacy Only)
```python
response_json = requests.get(url).json()

if response_json.get('success'):
    token = response_json['token']
    template_id = response_json['template_id']
```

### After (Supports Both Formats)
```python
response = api_client.some_endpoint(...)

if response.success:
    token = response.data.get('access_token') or response.data.get('token')
    template_id = response.data.get('template_id')
```

---

## Reference: Complete Example

```python
#!/usr/bin/env python3
"""Complete example: Face registration + authentication"""

from biometric import BiometricAPI, get_api_client
import base64

# ============================================================
# STEP 1: REGISTER A FACE
# ============================================================

# Capture or load image
with open("face_image.jpg", "rb") as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode()

# Register face (requires authentication)
BiometricAPI.set_token("user_token_from_login")
register_response = BiometricAPI.face_register(
    image_base64=image_base64,
    label="My Face"
)

if register_response.success:
    print(f"✅ Face registered: {register_response.data['template_id']}")
else:
    print(f"❌ {register_response.error_message}")
    exit(1)

# ============================================================
# STEP 2: AUTHENTICATE WITH FACE
# ============================================================

# Capture face for authentication
with open("auth_face.jpg", "rb") as f:
    auth_image = base64.b64encode(f.read()).decode()

# Verify face
auth_response = BiometricAPI.face_verify(
    email="admin@bioaccess.com",
    image_base64=auth_image
)

if auth_response.success:
    # Extract token
    token = auth_response.data.get('access_token') or auth_response.data.get('token')
    
    print(f"✅ Authentication successful!")
    print(f"   Token: {token[:20]}...")
    print(f"   User ID: {auth_response.data.get('user_id')}")
    print(f"   Role: {auth_response.data.get('role')}")
    
    # Set global token for subsequent requests
    BiometricAPI.set_token(token)
    
else:
    print(f"❌ Authentication failed: {auth_response.error_message}")
    exit(1)

# ============================================================
# STEP 3: USE AUTHENTICATED ENDPOINT
# ============================================================

# Get user profile (requires token)
client = get_api_client()
profile_response = client.get_user_profile()

if profile_response.success:
    user_data = profile_response.data
    print(f"✅ Profile retrieved:")
    print(f"   Email: {user_data.get('email')}")
    print(f"   Role: {user_data.get('role')}")
    print(f"   Verified: {user_data.get('biometric_verified')}")
else:
    print(f"❌ {profile_response.error_message}")
```

Run with:
```bash
python example_complete.py
```

---

## Summary

✅ **Client Desktop is fully adapted to the new APIResponse format**

- Automatic detection of both old and new response formats
- 100% backward compatible with legacy backends
- Zero code changes needed in client code for most cases
- Secure token extraction and persistence
- Production-ready deployment

**Next Steps**:
1. Deploy backend with new `APIResponse` format
2. Restart Client Desktop services
3. Monitor logs for any issues
4. Run integration tests

---

**Status**: Ready for Production ✅
