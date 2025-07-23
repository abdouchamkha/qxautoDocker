# Phase 2 Implementation - User Management & Authentication APIs

## ✅ Completed Features

### 🔐 Authentication System
- **User Registration** with automatic basic subscription (30-day trial)
- **User Login** with JWT token generation
- **Token Verification** and refresh functionality
- **Password Management** with strength validation
- **Secure Logout** with token invalidation

### 👤 User Management
- **Profile Management** (get/update user information)
- **User Statistics** with trading performance data
- **Activity Tracking** with pagination support
- **Account Settings** and preferences
- **Account Deletion** with confirmation

### 📋 Subscription Management
- **Subscription Tiers** (Basic, Premium, VIP)
- **Current Subscription** status and usage tracking
- **Subscription Limits** validation (accounts/sessions)
- **Subscription History** with pagination
- **Tier Information** and pricing

---

## 📊 Subscription Tiers

| Feature | Basic (Free) | Premium ($29/mo) | VIP ($99/mo) |
|---------|-------------|------------------|--------------|
| **Max Accounts** | 2 | 5 | 10 |
| **Active Sessions** | 1 | 3 | 5 |
| **Trial Period** | 30 days | - | - |
| **Telegram Signals** | Basic | Premium | VIP |
| **Support** | Standard | Priority | 24/7 |
| **Analytics** | Basic | Advanced | Advanced |
| **Custom Strategies** | ❌ | ✅ | ✅ |
| **Consultation** | ❌ | ❌ | ✅ |

---

## 🚀 API Endpoints

### Authentication Endpoints

#### `POST /api/v1/auth/register`
Register a new user account.

**Request:**
```json
{
    "username": "trader123",
    "email": "trader@example.com",
    "password": "SecurePass123!"
}
```

**Response:**
```json
{
    "success": true,
    "message": "User registered successfully",
    "data": {
        "user": {
            "id": 1,
            "username": "trader123",
            "email": "trader@example.com",
            "is_active": true
        },
        "subscription": {
            "subscription_type": "basic",
            "days_remaining": 30,
            "max_accounts": 2,
            "max_sessions": 1
        },
        "tokens": {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "Bearer"
        }
    }
}
```

#### `POST /api/v1/auth/login`
Authenticate user and get tokens.

**Request:**
```json
{
    "email": "trader@example.com",
    "password": "SecurePass123!"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Login successful",
    "data": {
        "user": { /* user data */ },
        "subscription": { /* subscription data */ },
        "tokens": { /* JWT tokens */ }
    }
}
```

#### `GET /api/v1/auth/verify`
Verify token validity (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "success": true,
    "message": "Token is valid",
    "data": {
        "user": { /* user data */ },
        "subscription": { /* subscription data */ },
        "token_valid": true
    }
}
```

#### `POST /api/v1/auth/change-password`
Change user password (requires authentication).

**Request:**
```json
{
    "current_password": "OldPass123!",
    "new_password": "NewSecurePass123!"
}
```

#### `POST /api/v1/auth/logout`
Logout user (requires authentication).

---

### User Management Endpoints

#### `GET /api/v1/users/profile`
Get user profile with statistics.

**Response:**
```json
{
    "success": true,
    "data": {
        "user": {
            "id": 1,
            "username": "trader123",
            "email": "trader@example.com"
        },
        "subscription": {
            "subscription_type": "basic",
            "days_remaining": 25,
            "max_accounts": 2,
            "max_sessions": 1
        },
        "statistics": {
            "total_accounts": 0,
            "active_sessions": 0,
            "total_trades": 0,
            "total_profit": 0.0
        }
    }
}
```

#### `PUT /api/v1/users/profile`
Update user profile information.

**Request:**
```json
{
    "username": "new_username",
    "email": "new_email@example.com"
}
```

#### `GET /api/v1/users/statistics`
Get detailed user trading statistics.

**Response:**
```json
{
    "success": true,
    "data": {
        "account_summary": {
            "total_accounts": 2,
            "demo_accounts": 1,
            "real_accounts": 1
        },
        "session_summary": {
            "active_sessions": 1,
            "inactive_sessions": 2,
            "total_sessions": 3
        },
        "trading_summary": {
            "total_trades": 150,
            "winning_trades": 95,
            "losing_trades": 55,
            "overall_win_rate": 63.33,
            "total_profit": 245.50
        }
    }
}
```

#### `DELETE /api/v1/users/account`
Delete user account permanently.

**Request:**
```json
{
    "password": "UserPassword123!",
    "confirmation": "DELETE_MY_ACCOUNT"
}
```

---

### Subscription Management Endpoints

#### `GET /api/v1/subscriptions/tiers`
Get available subscription tiers (no authentication required).

**Response:**
```json
{
    "success": true,
    "data": {
        "tiers": {
            "basic": {
                "name": "Basic",
                "max_accounts": 2,
                "max_sessions": 1,
                "price_monthly": 0,
                "features": ["Up to 2 trading accounts", "1 active session", "..."]
            },
            "premium": { /* premium tier details */ },
            "vip": { /* vip tier details */ }
        }
    }
}
```

#### `GET /api/v1/subscriptions/current`
Get current active subscription.

**Response:**
```json
{
    "success": true,
    "data": {
        "subscription": {
            "subscription_type": "basic",
            "start_date": "2024-01-15T10:00:00Z",
            "end_date": "2024-02-14T10:00:00Z",
            "days_remaining": 25
        },
        "tier_info": { /* tier details */ },
        "usage": {
            "accounts": {
                "current": 1,
                "limit": 2,
                "remaining": 1
            },
            "sessions": {
                "current": 0,
                "limit": 1,
                "remaining": 1
            }
        }
    }
}
```

#### `GET /api/v1/subscriptions/check-limits`
Check if user can create new resources.

**Response:**
```json
{
    "success": true,
    "data": {
        "subscription_valid": true,
        "limits": {
            "accounts": {
                "can_create": true,
                "current": 1,
                "limit": 2,
                "remaining": 1
            },
            "sessions": {
                "can_create": true,
                "current": 0,
                "limit": 1,
                "remaining": 1
            }
        }
    }
}
```

---

## 🧪 Testing

### Run Automated Tests
```bash
# Make sure the API server is running first
python app.py

# In another terminal, run the tests
python test_phase2.py
```

### Manual Testing with curl

#### Register a new user:
```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

#### Login:
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

#### Get user profile (replace TOKEN with actual token):
```bash
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer TOKEN"
```

#### Check subscription limits:
```bash
curl -X GET http://localhost:5000/api/v1/subscriptions/check-limits \
  -H "Authorization: Bearer TOKEN"
```

---

## 🔐 Authentication Flow

### 1. Registration Flow
```
User Registration → Email Validation → Password Strength Check 
→ Create User → Create Basic Subscription → Generate JWT Tokens
```

### 2. Login Flow
```
Email/Password → User Validation → Password Check 
→ Generate JWT Tokens → Return User + Subscription Data
```

### 3. Protected Endpoint Access
```
Request with JWT Token → Token Validation → User Lookup 
→ Subscription Check → Process Request
```

---

## 🔧 Security Features

### Password Requirements
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character

### JWT Token Management
- **Access Token**: 1 hour expiry (configurable)
- **Refresh Token**: 30 days expiry (configurable)
- Tokens include user ID for quick lookup
- Secure secret keys (auto-generated)

### Input Validation
- Email format validation
- Username length validation (3-50 characters)
- JSON schema validation
- SQL injection prevention

### Rate Limiting
- Built-in decorators for rate limiting
- User-based request limiting
- Error handling for excessive requests

---

## 📋 Error Handling

### Standard Error Response Format
```json
{
    "success": false,
    "error": "Error Type",
    "message": "Human-readable error message",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes
- **400**: Bad Request (invalid data)
- **401**: Unauthorized (invalid/missing token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found (resource doesn't exist)
- **409**: Conflict (duplicate data)
- **500**: Internal Server Error

---

## 🎯 Usage Examples

### Complete User Registration and Setup
```python
import requests

BASE_URL = "http://localhost:5000/api/v1"

# 1. Register user
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "myusername",
    "email": "my@email.com",
    "password": "SecurePass123!"
})

data = response.json()
token = data["data"]["tokens"]["access_token"]

# 2. Get user profile
headers = {"Authorization": f"Bearer {token}"}
profile = requests.get(f"{BASE_URL}/users/profile", headers=headers)

# 3. Check subscription limits
limits = requests.get(f"{BASE_URL}/subscriptions/check-limits", headers=headers)

print("User can create accounts:", limits.json()["data"]["limits"]["accounts"]["can_create"])
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Token Expired Errors
```bash
# Use refresh token to get new access token
curl -X POST http://localhost:5000/api/v1/auth/refresh \
  -H "Authorization: Bearer REFRESH_TOKEN"
```

#### 2. Password Validation Errors
Make sure passwords meet all requirements:
- Min 8 characters, uppercase, lowercase, number, special character

#### 3. Email Already Exists
Each email can only register once. Use a different email or login with existing account.

#### 4. Subscription Limits Reached
Check current usage with `/subscriptions/check-limits` endpoint. Upgrade subscription if needed.

---

## 📈 Next Steps (Phase 3)

Phase 2 provides the foundation for user management. The next phase will implement:

1. **Quotex Account Management** (`/api/v1/accounts/*`)
2. **Account Connection Testing**
3. **Balance Monitoring**
4. **Encrypted Credential Storage**

---

## ✅ Phase 2 Checklist

- [x] User registration with automatic subscription
- [x] JWT authentication system
- [x] Password strength validation
- [x] User profile management
- [x] Subscription tier system
- [x] Usage limits validation
- [x] Comprehensive error handling
- [x] API testing suite
- [x] Security middleware
- [x] Input validation
- [x] Rate limiting framework
- [x] Standardized responses

**Phase 2 Status**: ✅ **COMPLETE**

Ready to proceed to **Phase 3: Quotex Account Management APIs** 