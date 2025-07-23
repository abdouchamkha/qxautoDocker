#!/usr/bin/env python3
"""
Test script for Phase 2 - User Management & Authentication APIs
This script tests all the implemented endpoints to ensure they work correctly.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
HEADERS = {"Content-Type": "application/json"}

# Test data
TEST_USER = {
    "username": "testuser2",
    "email": "test2@example.com",
    "password": "SecurePass123!"
}

# Global variables for testing
access_token = None
user_id = None


def print_test_header(title):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f" Testing: {title}")
    print(f"{'='*60}")


def print_test_result(test_name, success, response=None, error=None):
    """Print test result with formatting."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    
    if response and isinstance(response, dict):
        if 'message' in response:
            print(f"    Message: {response['message']}")
    
    if error:
        print(f"    Error: {error}")
    
    print()


def make_request(method, endpoint, data=None, auth_token=None):
    """Make HTTP request with error handling."""
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        try:
            response_data = response.json()
        except:
            response_data = {"status_code": response.status_code, "text": response.text}
        
        return response.status_code, response_data
        
    except requests.exceptions.ConnectionError:
        return None, {"error": "Connection failed - is the server running?"}
    except Exception as e:
        return None, {"error": str(e)}


def test_health_check():
    """Test API health check."""
    print_test_header("Health Check")
    
    status_code, response = make_request("GET", "/health")
    
    if status_code == 200 and response.get("success"):
        print_test_result("Health check", True, response)
        return True
    else:
        print_test_result("Health check", False, response)
        return False


def test_api_info():
    """Test API information endpoint."""
    print_test_header("API Information")
    
    status_code, response = make_request("GET", "/")
    
    if status_code == 200 and response.get("success"):
        print_test_result("API info", True, response)
        return True
    else:
        print_test_result("API info", False, response)
        return False


def test_subscription_tiers():
    """Test getting subscription tiers (no auth required)."""
    print_test_header("Subscription Tiers")
    
    status_code, response = make_request("GET", "/subscriptions/tiers")
    
    if status_code == 200 and response.get("success"):
        tiers = response.get("data", {}).get("tiers", {})
        print_test_result(f"Get subscription tiers ({len(tiers)} tiers)", True, response)
        return True
    else:
        print_test_result("Get subscription tiers", False, response)
        return False


def test_user_registration():
    """Test user registration."""
    global access_token, user_id
    
    print_test_header("User Registration")
    
    status_code, response = make_request("POST", "/auth/register", TEST_USER)
    
    if status_code == 201 and response.get("success"):
        user_data = response.get("data", {})
        tokens = user_data.get("tokens", {})
        access_token = tokens.get("access_token")
        user_id = user_data.get("user", {}).get("id")
        
        print_test_result("User registration", True, response)
        print(f"    User ID: {user_id}")
        print(f"    Token obtained: {'Yes' if access_token else 'No'}")
        return True
    else:
        print_test_result("User registration", False, response)
        return False


def test_user_login():
    """Test user login."""
    global access_token, user_id
    
    print_test_header("User Login")
    
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    status_code, response = make_request("POST", "/auth/login", login_data)
    
    if status_code == 200 and response.get("success"):
        user_data = response.get("data", {})
        tokens = user_data.get("tokens", {})
        access_token = tokens.get("access_token")
        user_id = user_data.get("user", {}).get("id")
        
        print_test_result("User login", True, response)
        return True
    else:
        print_test_result("User login", False, response)
        return False


def test_token_verification():
    """Test token verification."""
    print_test_header("Token Verification")
    
    status_code, response = make_request("GET", "/auth/verify", auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        print_test_result("Token verification", True, response)
        return True
    else:
        print_test_result("Token verification", False, response)
        return False


def test_get_profile():
    """Test getting user profile."""
    print_test_header("User Profile")
    
    status_code, response = make_request("GET", "/users/profile", auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        profile_data = response.get("data", {})
        user = profile_data.get("user", {})
        subscription = profile_data.get("subscription", {})
        
        print_test_result("Get user profile", True, response)
        print(f"    Username: {user.get('username')}")
        print(f"    Email: {user.get('email')}")
        print(f"    Subscription: {subscription.get('subscription_type') if subscription else 'None'}")
        return True
    else:
        print_test_result("Get user profile", False, response)
        return False


def test_update_profile():
    """Test updating user profile."""
    print_test_header("Update Profile")
    
    update_data = {
        "username": "testuser2_updated"
    }
    
    status_code, response = make_request("PUT", "/users/profile", update_data, auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        print_test_result("Update user profile", True, response)
        return True
    else:
        print_test_result("Update user profile", False, response)
        return False


def test_get_user_statistics():
    """Test getting user statistics."""
    print_test_header("User Statistics")
    
    status_code, response = make_request("GET", "/users/statistics", auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        stats = response.get("data", {})
        print_test_result("Get user statistics", True, response)
        print(f"    Total accounts: {stats.get('account_summary', {}).get('total_accounts', 0)}")
        print(f"    Total sessions: {stats.get('session_summary', {}).get('total_sessions', 0)}")
        return True
    else:
        print_test_result("Get user statistics", False, response)
        return False


def test_subscription_management():
    """Test subscription management."""
    print_test_header("Subscription Management")
    
    # Test getting user subscriptions
    status_code, response = make_request("GET", "/subscriptions/", auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        print_test_result("Get user subscriptions", True, response)
        
        # Test getting current subscription
        status_code2, response2 = make_request("GET", "/subscriptions/current", auth_token=access_token)
        
        if status_code2 == 200 and response2.get("success"):
            print_test_result("Get current subscription", True, response2)
            
            # Test checking subscription limits
            status_code3, response3 = make_request("GET", "/subscriptions/check-limits", auth_token=access_token)
            
            if status_code3 == 200 and response3.get("success"):
                limits = response3.get("data", {}).get("limits", {})
                print_test_result("Check subscription limits", True, response3)
                print(f"    Can create accounts: {limits.get('accounts', {}).get('can_create', False)}")
                print(f"    Can create sessions: {limits.get('sessions', {}).get('can_create', False)}")
                return True
            else:
                print_test_result("Check subscription limits", False, response3)
                return False
        else:
            print_test_result("Get current subscription", False, response2)
            return False
    else:
        print_test_result("Get user subscriptions", False, response)
        return False


def test_change_password():
    """Test changing password."""
    print_test_header("Change Password")
    
    change_data = {
        "current_password": TEST_USER["password"],
        "new_password": "NewSecurePass123!"
    }
    
    status_code, response = make_request("POST", "/auth/change-password", change_data, auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        print_test_result("Change password", True, response)
        # Update password for future tests
        TEST_USER["password"] = change_data["new_password"]
        return True
    else:
        print_test_result("Change password", False, response)
        return False


def test_logout():
    """Test user logout."""
    print_test_header("User Logout")
    
    status_code, response = make_request("POST", "/auth/logout", auth_token=access_token)
    
    if status_code == 200 and response.get("success"):
        print_test_result("User logout", True, response)
        return True
    else:
        print_test_result("User logout", False, response)
        return False


def test_invalid_requests():
    """Test invalid requests to ensure proper error handling."""
    print_test_header("Error Handling")
    
    # Test login with wrong credentials
    wrong_login = {
        "email": TEST_USER["email"],
        "password": "wrongpassword"
    }
    
    status_code, response = make_request("POST", "/auth/login", wrong_login)
    
    if status_code == 401 and not response.get("success"):
        print_test_result("Invalid login credentials", True, response)
    else:
        print_test_result("Invalid login credentials", False, response)
    
    # Test accessing protected endpoint without token
    status_code, response = make_request("GET", "/users/profile")
    
    if status_code == 401 and not response.get("success"):
        print_test_result("Unauthorized access protection", True, response)
        return True
    else:
        print_test_result("Unauthorized access protection", False, response)
        return False


def run_all_tests():
    """Run all tests in sequence."""
    print("Starting Phase 2 API Tests...")
    print(f"Testing against: {BASE_URL}")
    print(f"Test started at: {datetime.now()}")
    
    # Track test results
    tests_passed = 0
    total_tests = 0
    
    test_functions = [
        test_health_check,
        test_api_info,
        test_subscription_tiers,
        test_user_registration,
        test_token_verification,
        test_get_profile,
        test_update_profile,
        test_get_user_statistics,
        test_subscription_management,
        test_change_password,
        test_logout,
        test_user_login,  # Re-login with new password
        test_invalid_requests,
    ]
    
    for test_func in test_functions:
        total_tests += 1
        if test_func():
            tests_passed += 1
        time.sleep(0.5)  # Brief pause between tests
    
    # Print summary
    print(f"\n{'='*60}")
    print(f" TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    print(f"Success rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print(f"🎉 All tests passed! Phase 2 implementation is working correctly.")
    else:
        print(f"⚠️  Some tests failed. Please check the implementation.")
    
    print(f"Test completed at: {datetime.now()}")


if __name__ == '__main__':
    run_all_tests() 