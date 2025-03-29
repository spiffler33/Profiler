"""
Admin Endpoint Test Script

This script tests if admin endpoints exist in the app.py file by checking the route registration.
"""

import os
import sys
import importlib.util
import inspect

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def test_admin_endpoints():
    """Check if admin endpoints are registered in the app"""
    # Import app.py directly from file
    app_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app.py')
    
    # Check if app.py exists
    if not os.path.exists(app_path):
        print(f"❌ app.py not found at {app_path}")
        return False
    
    # Load app.py as a module
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    # Get the Flask app instance
    app = app_module.app
    
    # Check if app is a Flask app
    if not hasattr(app, 'url_map'):
        print("❌ app is not a Flask app")
        return False
    
    # Print all available routes
    print("\n=== All Routes in the Application ===")
    for rule in app.url_map.iter_rules():
        print(f"- {rule} → {rule.endpoint}")
    
    # Check for admin endpoints
    print("\n=== Admin Routes ===")
    admin_routes = [rule for rule in app.url_map.iter_rules() if 'admin' in str(rule)]
    
    if not admin_routes:
        print("❌ No admin routes found in the application")
        return False
    
    # Print admin routes
    for rule in admin_routes:
        print(f"- {rule} → {rule.endpoint}")
    
    # Check for API v2 admin endpoints
    print("\n=== API v2 Admin Routes ===")
    api_v2_admin_routes = [rule for rule in app.url_map.iter_rules() if '/api/v2/admin' in str(rule)]
    
    if not api_v2_admin_routes:
        print("❌ No API v2 admin routes found in the application")
        print("The frontend components expect these endpoints to exist")
        return False
    
    # Print API v2 admin routes
    for rule in api_v2_admin_routes:
        print(f"- {rule} → {rule.endpoint}")
    
    # Check for authentication setup
    print("\n=== Authentication Setup ===")
    
    # Check if HTTPBasicAuth is being used
    if hasattr(app_module, 'auth') and app_module.auth is not None:
        print("✅ HTTPBasicAuth is set up")
        
        # Check verify_password function
        if hasattr(app_module, 'verify_password'):
            print("✅ verify_password function exists")
            
            # Get the source code of verify_password
            source = inspect.getsource(app_module.verify_password)
            print("\nverify_password implementation:")
            print(source)
            
            # Check if authentication is bypassed
            if "return True" in source:
                print("⚠️ Authentication is bypassed for development")
            
            # Test the verify_password function
            test_result = app_module.verify_password("admin", "admin")
            print(f"Test verify_password('admin', 'admin'): {test_result}")
    else:
        print("❌ HTTPBasicAuth is not set up")
    
    print("\n=== Integration Status ===")
    
    # Check if we found the expected admin endpoints for frontend integration
    required_endpoints = [
        '/api/v2/admin/parameters',
        '/api/v2/admin/parameters/<path:path>',
        '/api/v2/admin/parameters/history/<path:path>',
        '/api/v2/admin/parameters/impact/<path:path>',
        '/api/v2/admin/parameters/related/<path:path>',
        '/api/v2/admin/parameters/audit',
        '/api/v2/admin/profiles',
        '/api/v2/admin/parameters/user/<user_id>',
        '/api/v2/admin/parameters/user/<user_id>/reset'
    ]
    
    # Convert rules to strings for comparison
    route_strings = [str(rule) for rule in app.url_map.iter_rules()]
    
    # Check each required endpoint
    for endpoint in required_endpoints:
        found = any(endpoint in route for route in route_strings)
        if found:
            print(f"✅ Found required endpoint: {endpoint}")
        else:
            print(f"❌ Missing required endpoint: {endpoint}")
    
    return True

def main():
    """Main function"""
    print("Testing admin endpoints in the application")
    test_admin_endpoints()

if __name__ == "__main__":
    main()