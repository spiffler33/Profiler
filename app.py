from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, Response, send_file, abort, send_from_directory, current_app, make_response
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
import os
import logging
import json
import base64
from datetime import datetime
import uuid
import functools
import time
import traceback

# Import our custom modules
from models.database_profile_manager import DatabaseProfileManager
from models.question_repository import QuestionRepository
from models.goal_models import GoalManager
from models.goal_probability import GoalProbabilityAnalyzer
from models.goal_adjustment import GoalAdjustmentRecommender
from services.goal_adjustment_service import GoalAdjustmentService
from services.question_service import QuestionService
from services.llm_service import LLMService
from services.profile_analytics_service import ProfileAnalyticsService
from services.goal_service import GoalService
from services.financial_parameter_service import FinancialParameterService, get_financial_parameter_service
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Enable CORS for all routes
CORS(app)

# Initialize configuration for the app
Config.init_app(app)

@app.route('/api/v2/check_server')
def check_server():
    """Simple endpoint to verify the server is running without auth"""
    app.logger.info("check_server endpoint accessed!")
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v2/debug/goal_probability/<goal_id>')
def debug_goal_probability(goal_id):
    """Debug endpoint to view raw goal probability data"""
    try:
        # Get goal service
        goal_service = app.config.get('goal_service', GoalService())
        
        # Get the goal with all probability details
        goal = goal_service.get_goal(goal_id, legacy_mode=False, include_probability_details=True)
        if not goal:
            return jsonify({
                'error': 'Goal not found',
                'goal_id': goal_id
            }), 404
            
        # Extract probability information
        probability_info = {
            'goal_id': goal_id,
            'goal_title': goal.get('title', 'Unknown'),
            'goal_category': goal.get('category', 'Unknown'),
            'goal_success_probability': goal.get('goal_success_probability'),
            'goal_success_probability_type': type(goal.get('goal_success_probability')).__name__,
            'probability_raw': goal.get('goal_success_probability'),
            'has_probability': 'goal_success_probability' in goal,
            'has_probability_not_none': goal.get('goal_success_probability') is not None,
            'probability_details': {
                'probability_metrics': goal.get('probability_metrics', {}),
                'time_metrics': goal.get('time_metrics', {}),
                'probability_meta': goal.get('probability_meta', {})
            },
            'template_render_test': {
                'test1': f"{goal.get('goal_success_probability')}",
                'test2': f"{goal.get('goal_success_probability') if goal.get('goal_success_probability') else '--'}",
                'test3': f"{goal.get('goal_success_probability') if goal.get('goal_success_probability') is not None else '--'}"
            }
        }
        
        # Log the diagnostics
        app.logger.info(f"Goal probability diagnostics for {goal_id}: {probability_info}")
        
        return jsonify(probability_info)
    except Exception as e:
        app.logger.error(f"Error in debug_goal_probability: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'goal_id': goal_id
        }), 500

app.logger.info(f"Application starting with DEV_MODE={Config.DEV_MODE}")

# @app.route('/')
# def index_page():
#     return """
#     <html>
#     <head><title>Financial Profiler App</title></head>
#     <body>
#         <h1>Financial Profiler Application</h1>
#         <p>The server is running correctly.</p>
#         <p><a href="/api/v2/check_server">Check Server API</a></p>
#         <p><a href="/api/v2/admin/test">Admin Test API</a></p>
#     </body>
#     </html>
#     """

@app.before_request
def log_browser_request():
    app.logger.info(f"Received request from: {request.user_agent}")
    app.logger.info(f"Path: {request.path}")
    app.logger.info(f"Method: {request.method}")
    app.logger.info(f"Headers: {dict(request.headers)}")

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(f"404 error for path: {request.path}")
    return jsonify({
        'error': '404 Not Found',
        'path': request.path,
        'message': 'The requested URL was not found on the server'
    }), 404

# Print debug information at startup
print("\n====== APPLICATION STARTUP ======")
import sys
print(f"Python version: {sys.version}")
print(f"Running file: {__file__}")
print(f"Application name: {__name__}")
print(f"Static folder: {app.static_folder}")
print(f"Static URL path: {app.static_url_path}")
print("==================================\n")

# Print security-related configuration
print("\n===== APP CONFIGURATION =====")
security_related = ['PREFERRED_URL_SCHEME', 'SERVER_NAME', 'APPLICATION_ROOT',
                   'SESSION_COOKIE_SECURE', 'PERMANENT_SESSION_LIFETIME',
                   'SESSION_COOKIE_HTTPONLY', 'SESSION_COOKIE_SAMESITE',
                   'DEBUG', 'TESTING', 'PROPAGATE_EXCEPTIONS']
for key in security_related:
    if key in app.config:
        print(f"{key}: {app.config[key]}")
print("=============================\n")

# Register mock API endpoints for testing
try:
    from api.v2.mock_endpoints import mock_api
    app.register_blueprint(mock_api)
    logging.info("Mock API endpoints registered for testing")
except ImportError as e:
    logging.warning(f"Could not register mock API endpoints: {str(e)}")

# Import centralized authentication
from auth_utils import auth

"""
# Improved admin_required decorator
def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # First check request path to see if it should be exempted
        path = request.path

        # Exempt paths that should never require auth
        exempt_prefixes = ['/static/', '/js/', '/debug-', '/no-auth-']
        exempt_suffixes = ['.js', '.css', '.html', '.ico', '.png', '.jpg', '.svg', '.gif']
        exempt_paths = [
            '/loading_state_manager_js',
            '/goal_form_probability_js',
            '/inline_test',
            '/test_frontend_components',
            '/api/v2/public/debug',
            '/api/v2/test/auth_headers',
            '/api/v2/direct-auth-test',
            '/debug-info',
            '/no-auth-test'
        ]

        # Check if path is exempt
        is_exempt = False

        # Check exact matches
        if path in exempt_paths:
            is_exempt = True
            app.logger.info(f"Path {path} exactly matches exempt path")

        # Check prefixes
        if not is_exempt:
            for prefix in exempt_prefixes:
                if path.startswith(prefix):
                    is_exempt = True
                    app.logger.info(f"Path {path} matches exempt prefix {prefix}")
                    break

        # Check suffixes
        if not is_exempt:
            for suffix in exempt_suffixes:
                if path.endswith(suffix):
                    is_exempt = True
                    app.logger.info(f"Path {path} matches exempt suffix {suffix}")
                    break

        # If path is exempt, skip authentication
        if is_exempt:
            app.logger.info(f"Bypassing authentication for exempt path: {path}")
            return f(*args, **kwargs)

        # Then check DEV_MODE
        if getattr(Config, 'DEV_MODE', False):
            # Log the authentication bypass
            app.logger.info(f"DEV_MODE: Authentication bypassed for {path}")
            return f(*args, **kwargs)

        # If not exempt or DEV_MODE, apply normal authentication
        # This uses the auth.login_required decorator from flask_httpauth
        auth_decorator = auth.login_required(f)
        return auth_decorator(*args, **kwargs)

    return decorated
"""

def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Check DEV_MODE first
        if getattr(Config, 'DEV_MODE', False):
            app.logger.info(f"DEV_MODE: Authentication bypassed for {request.path}")
            return f(*args, **kwargs)

        # Then use auth.login_required
        return auth.login_required(f)(*args, **kwargs)
    return decorated

# Add test routes for Phase 1 and 2 implementations
@app.route('/test_financial_dashboard')
def test_financial_dashboard():
    """Test route for financial overview dashboard component"""
    logging.info("Test route accessed: /test_financial_dashboard")
    return send_file('static/test_financial_dashboard.html')

@app.route('/test_api_service')
def test_api_service():
    """Test route for API service"""
    logging.info("Test route accessed: /test_api_service")
    return send_file('static/test_api_service.html')

@app.route('/test_question_flow_api')
def test_question_flow_api():
    """Test route for question flow API integration"""
    logging.info("Test route accessed: /test_question_flow_api")
    return send_file('static/test_question_flow_api.html')

# Add routes for testing
@app.route('/test_frontend_components')
def test_frontend_components():
    """Test route for checking frontend components"""
    logging.info("Test route accessed: /test_frontend_components")

    # Test if JavaScript files exist
    import os.path
    js_files = [
        'static/js/services/LoadingStateManager.js',
        'static/js/goal_form_probability.js',
        'static/js/test_loading_states.js',
        'static/js/test_api_integration.js'
    ]

    file_status = {}
    for js_file in js_files:
        file_path = os.path.join(app.root_path, js_file)
        file_status[js_file] = os.path.isfile(file_path)
        logging.info(f"Checking file {js_file}: {'Exists' if file_status[js_file] else 'Not found'}")

    return jsonify({
        'status': 'success',
        'files_checked': file_status,
        'message': 'Frontend component test completed. Check logs for details.'
    })

# Special direct file serving route for testing
@app.route('/serve_test_file/<path:filepath>')
def serve_test_file(filepath):
    """Directly serve a test file from the application root"""
    import os
    from flask import send_file, abort, Response

    full_path = os.path.join(app.root_path, filepath)
    logging.info(f"Attempting to serve file: {full_path}")

    if not os.path.isfile(full_path):
        logging.error(f"File not found: {full_path}")
        return abort(404)

    logging.info(f"Serving file: {full_path}")
    try:
        return send_file(full_path)
    except Exception as e:
        logging.error(f"Error serving file {full_path}: {str(e)}")
        return Response(f"Error serving file: {str(e)}", status=500)

# Direct content routes for testing
@app.route('/loading_state_manager_js')
def loading_state_manager_js():
    """Directly serve the LoadingStateManager.js file content"""
    import os

    js_path = os.path.join(app.root_path, 'static', 'js', 'services', 'LoadingStateManager.js')

    if not os.path.isfile(js_path):
        logging.error(f"LoadingStateManager.js not found at {js_path}")
        return Response("File not found", status=404)

    try:
        with open(js_path, 'r') as f:
            content = f.read()

        return Response(content, mimetype='application/javascript')
    except Exception as e:
        logging.error(f"Error reading LoadingStateManager.js: {str(e)}")
        return Response(f"Error: {str(e)}", status=500)

@app.route('/goal_form_probability_js')
def goal_form_probability_js():
    """Directly serve the goal_form_probability.js file content"""
    import os

    js_path = os.path.join(app.root_path, 'static', 'js', 'goal_form_probability.js')

    if not os.path.isfile(js_path):
        logging.error(f"goal_form_probability.js not found at {js_path}")
        return Response("File not found", status=404)

    try:
        with open(js_path, 'r') as f:
            content = f.read()

        return Response(content, mimetype='application/javascript')
    except Exception as e:
        logging.error(f"Error reading goal_form_probability.js: {str(e)}")
        return Response(f"Error: {str(e)}", status=500)

@app.route('/inline_test')
def inline_test():
    """Directly serve an inline test page"""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inline Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .test-box {
                border: 1px solid #ccc;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Inline Test Page</h1>
        <p>This page is served directly by Flask.</p>

        <div class="test-box">
            <h2>Test Results</h2>
            <p id="result">JavaScript is functioning correctly</p>
        </div>

        <script>
            document.getElementById('result').className = 'success';
            document.getElementById('result').textContent = 'JavaScript is functioning correctly';
        </script>
    </body>
    </html>
    """

    return Response(html, mimetype='text/html')

# Create explicit routes to serve static files without auth
@app.route('/static/<path:filename>')
def serve_static(filename):
    app.logger.debug(f"Serving static file: {filename}")
    return send_from_directory(app.static_folder, filename)

# Add specific routes for JavaScript files without auth
@app.route('/js/<path:filename>')
def serve_js(filename):
    app.logger.debug(f"Serving JS file: {filename}")
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/js/services/<path:filename>')
def serve_js_services(filename):
    app.logger.debug(f"Serving JS services file: {filename}")
    return send_from_directory(os.path.join(app.static_folder, 'js', 'services'), filename)

# Debug endpoints
@app.route('/debug-info')
def debug_info():
    app.logger.info("DEBUG INFO ENDPOINT ACCESSED")
    app.logger.info(f"Request path: {request.path}")
    app.logger.info(f"Request headers: {request.headers}")

    try:
        result = {
            'environment': {k: v for k, v in os.environ.items() if not k.startswith('_')},
            'flask_config': {k: str(v) for k, v in app.config.items() if isinstance(v, (str, int, float, bool, list, dict))},
            'request_headers': dict(request.headers),
            'static_folder': app.static_folder,
            'static_url_path': app.static_url_path,
            'dev_mode': getattr(Config, 'DEV_MODE', False)
        }
        app.logger.info("Debug info endpoint returning successfully")
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/debug-static/<path:filename>')
def debug_serve_static(filename):
    app.logger.info(f"Attempting to serve static file via debug route: {filename}")
    static_folder = app.static_folder
    app.logger.info(f"Static folder path: {static_folder}")
    return send_from_directory(static_folder, filename)

@app.route('/no-auth-test')
def no_auth_test():
    app.logger.info("NO AUTH TEST ENDPOINT ACCESSED")
    return "This route should have no authentication"

# Initialize Monte Carlo cache system
try:
    from models.monte_carlo.cache import initialize_cache, configure_cache, get_cache_stats

    # Configure cache based on app config
    if hasattr(Config, 'MONTE_CARLO_CACHE_SIZE'):
        max_cache_size = Config.MONTE_CARLO_CACHE_SIZE
    else:
        max_cache_size = 100

    if hasattr(Config, 'MONTE_CARLO_CACHE_TTL'):
        cache_ttl = Config.MONTE_CARLO_CACHE_TTL
    else:
        cache_ttl = 3600  # 1 hour

    if hasattr(Config, 'MONTE_CARLO_CACHE_SAVE_INTERVAL'):
        save_interval = Config.MONTE_CARLO_CACHE_SAVE_INTERVAL
    else:
        save_interval = 300  # 5 minutes

    if hasattr(Config, 'MONTE_CARLO_CACHE_DIR'):
        cache_dir = Config.MONTE_CARLO_CACHE_DIR
    else:
        cache_dir = None  # Use default

    # Configure and initialize the cache
    configure_cache(
        max_size=max_cache_size,
        ttl=cache_ttl,
        save_interval=save_interval,
        cache_dir=cache_dir
    )
    initialize_cache()

    app.logger.info("Monte Carlo cache system initialized")

except Exception as e:
    app.logger.warning(f"Failed to initialize Monte Carlo cache: {e}")
    app.logger.warning("Monte Carlo simulations will still work but without persistence")

# Import and register API blueprints
from api.v2.visualization_data import visualization_api
from api.v2.goal_probability_api import goal_probability_api
from api.v2.parameter_api import parameter_api
from api.v2.question_flow_api import question_flow_api
from api.v2.admin_parameters_api import admin_parameters_api
from api.v2.admin_health_api import admin_health_api

# Import consolidated Monte Carlo API modules
from models.monte_carlo.api_integration import create_simulation_endpoint, create_cache_clear_endpoint

# Register API v2 blueprints
app.register_blueprint(visualization_api, url_prefix='/api/v2')
app.register_blueprint(goal_probability_api, url_prefix='/api/v2')
app.register_blueprint(parameter_api, url_prefix='/api/v2')
app.register_blueprint(question_flow_api, url_prefix='/api/v2')
app.register_blueprint(admin_parameters_api, url_prefix='/api/v2')
app.register_blueprint(admin_health_api, url_prefix='/api/v2')

# Add a simple test endpoint to check if admin routes work
@app.route('/api/v2/admin/test', methods=['GET'])
@admin_required
def admin_test_endpoint():
    """Simple test endpoint for admin API."""
    return jsonify({
        'status': 'success',
        'message': 'Admin test endpoint is working',
        'timestamp': datetime.now().isoformat(),
        'auth_user': auth.current_user(),
        'dev_mode': getattr(Config, 'DEV_MODE', False)
    })

# Add a diagnostic endpoint to check auth headers and configuration
@app.route('/api/v2/test/auth_headers', methods=['GET'])
def test_auth_headers():
    """Debug endpoint to check authentication headers and configuration"""
    # Explicitly log access to this endpoint
    app.logger.info(f"Auth headers debug endpoint accessed from {request.remote_addr}")

    auth_header = request.headers.get('Authorization', 'None')

    # Only show first 10 chars of auth header to avoid leaking credentials in logs
    safe_auth_header = auth_header[:10] + '...' if auth_header != 'None' and len(auth_header) > 10 else auth_header

    # Get a subset of headers for debugging
    safe_headers = {}
    for key, value in request.headers.items():
        if key.lower() in ['host', 'user-agent', 'accept', 'content-type']:
            safe_headers[key] = value
        elif key.lower() == 'authorization':
            safe_headers[key] = safe_auth_header

    # Get environment variables
    env_dev_mode = os.environ.get('DEV_MODE', 'Not set')
    env_flask_env = os.environ.get('FLASK_ENV', 'Not set')

    return jsonify({
        'dev_mode': getattr(Config, 'DEV_MODE', False),
        'auth_header': safe_auth_header,
        'has_valid_format': auth_header.startswith('Basic ') if auth_header != 'None' else False,
        'request_headers': safe_headers,
        'auth_configured': hasattr(Config, 'ADMIN_USERNAME') and hasattr(Config, 'ADMIN_PASSWORD'),
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'DEV_MODE': env_dev_mode,
            'FLASK_ENV': env_flask_env,
            'DEBUG': os.environ.get('FLASK_DEBUG', 'Not set')
        },
        'request_path': request.path,
        'request_method': request.method
    })

# Add a completely public debug endpoint that requires no auth
@app.route('/api/v2/public/debug', methods=['GET'])
def public_debug_endpoint():
    """Completely public endpoint for debugging middleware issues"""
    # Log detailed information about the request
    app.logger.info(f"Received request to public debug endpoint")
    app.logger.info(f"Request headers: {dict(request.headers)}")

    # Get auth configuration
    dev_mode = getattr(Config, 'DEV_MODE', False)
    admin_username = getattr(Config, 'ADMIN_USERNAME', 'Not configured')
    has_admin_password = hasattr(Config, 'ADMIN_PASSWORD')

    # Check if environment variables are set
    env_dev_mode = os.environ.get('DEV_MODE', 'Not set')

    return jsonify({
        'status': 'success',
        'message': 'Public debug endpoint accessible',
        'timestamp': datetime.now().isoformat(),
        'config': {
            'dev_mode': dev_mode,
            'admin_username': admin_username,
            'has_admin_password': has_admin_password
        },
        'environment': {
            'DEV_MODE': env_dev_mode,
            'FLASK_ENV': os.environ.get('FLASK_ENV', 'Not set'),
            'FLASK_DEBUG': os.environ.get('FLASK_DEBUG', 'Not set')
        }
    })

# Simple auth test endpoint with no middleware involved
@app.route('/api/v2/direct-auth-test', methods=['GET'])
def direct_auth_test():
    """
    Direct auth test endpoint that uses DEV_MODE directly without middleware
    """
    # Log the request
    app.logger.info(f"Direct auth test accessed from {request.remote_addr}")

    # Check for Authorization header
    auth_header = request.headers.get('Authorization', 'None')

    # Only show first 10 chars of auth header to avoid leaking credentials
    safe_auth_header = auth_header[:10] + '...' if auth_header != 'None' and len(auth_header) > 10 else auth_header

    # Check DEV_MODE
    dev_mode = getattr(Config, 'DEV_MODE', False)

    # If DEV_MODE is enabled, always return success
    if dev_mode:
        return jsonify({
            'status': 'success',
            'message': 'Authentication bypassed due to DEV_MODE=True',
            'dev_mode': True,
            'auth_header': safe_auth_header,
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())
        })

    # Otherwise, check for valid credentials
    if auth_header != 'None' and auth_header.startswith('Basic '):
        try:
            # Decode credentials
            auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = auth_decoded.split(':', 1)

            # Check credentials
            if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
                return jsonify({
                    'status': 'success',
                    'message': 'Authentication successful',
                    'dev_mode': False,
                    'auth_header': safe_auth_header,
                    'timestamp': datetime.now().isoformat(),
                    'request_id': str(uuid.uuid4())
                })
        except Exception as e:
            app.logger.error(f"Error decoding auth header: {str(e)}")

    # If we get here, authentication failed
    return jsonify({
        'status': 'error',
        'message': 'Authentication required',
        'dev_mode': dev_mode,
        'auth_header': safe_auth_header,
        'timestamp': datetime.now().isoformat(),
        'request_id': str(uuid.uuid4())
    }), 401

# Register a route that uses our consolidated API functions
@app.route('/api/v2/test/simulation/<goal_id>', methods=['GET'])
def test_simulation_endpoint(goal_id):
    """Test endpoint using the consolidated simulation module."""
    # Get goal service from app config
    goal_service_instance = app.config.get('goal_service', GoalService())

    # Parse request parameters
    params = request.args.to_dict()
    params['goal_id'] = goal_id

    # Validate goal_id format
    try:
        uuid_obj = uuid.UUID(goal_id)
    except ValueError:
        return jsonify({
            'error': 'Invalid goal ID format',
            'message': 'Goal ID must be a valid UUID'
        }), 400

    # Get goal from service
    try:
        goal = goal_service_instance.get_goal(goal_id)
        if not goal:
            return jsonify({
                'error': 'Goal not found',
                'message': f'No goal found with ID {goal_id}'
            }), 404
    except Exception as e:
        app.logger.error(f"Error retrieving goal {goal_id} in simulation endpoint: {str(e)}")
        return jsonify({
            'error': 'Error retrieving goal',
            'message': str(e) 
        }), 500

    # Use our consolidated functions
    from models.monte_carlo.simulation import safely_get_simulation_data

    # Get simulation data
    simulation_data = safely_get_simulation_data(goal)

    # Prepare response data
    response = {
        'success_probability': simulation_data.get('success_probability', 0.0),
        'goal_id': goal_id,
        'target_amount': goal.get('target_amount', 0),
        'current_amount': goal.get('current_amount', 0),
        'time_horizon': goal.get('timeframe_years', 0)
    }

    # Cache the response
    from models.monte_carlo.simulation import cache_response
    cache_key = f"test_simulation_{goal_id}"
    cache_response(cache_key, response)

    return jsonify(response), 200

# The old middleware has been removed in favor of the direct checks in the admin_required decorator

# Serve any static file or HTML file directly with its proper mimetype
@app.route('/<path:filename>')
def serve_any_static(filename):
    # Only serve files with static extensions
    if any(filename.endswith(ext) for ext in ['.js', '.css', '.html', '.ico', '.png', '.jpg']):
        app.logger.info(f"Attempting to serve file: {filename}")
        return send_from_directory(app.root_path, filename)
    abort(404)

# Add detailed request logging
@app.before_request
def log_request_details():
    app.logger.info(f"Request: {request.method} {request.path}")
    app.logger.info(f"Remote address: {request.remote_addr}")
    # Don't log all headers to avoid sensitive info in logs
    important_headers = ['User-Agent', 'Referer', 'Accept', 'Content-Type']
    headers_to_log = {k: v for k, v in request.headers.items() if k in important_headers}
    app.logger.info(f"Important headers: {headers_to_log}")

# Print all registered routes for debugging
print("\n=== Registered Routes ===")
with app.app_context():
    route_list = []
    for rule in app.url_map.iter_rules():
        route_list.append({
            'endpoint': rule.endpoint,
            'methods': ','.join(rule.methods),
            'rule': str(rule)
        })

    for route in sorted(route_list, key=lambda x: x['rule']):
        print(f"{route['rule']} -> {route['endpoint']} [{route['methods']}]")
    print("===========================\n")


# Regular Flask route for the homepage
@app.route('/')
def index():
    """Render the main index page"""
    return render_template('index.html')

@app.route('/create_profile', methods=['GET', 'POST'])
def create_profile():
    """
    GET: Render the profile creation page
    POST: Create a new profile via API
    """
    if request.method == 'GET':
        return render_template('profile_create.html')
    
    # Handle POST request to create profile
    try:
        # Get the profile data from the request JSON
        profile_data = request.get_json()
        if not profile_data:
            return jsonify({
                'success': False,
                'error': 'Missing profile data'
            }), 400
            
        # Validate required fields
        if 'name' not in profile_data or not profile_data['name']:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400
            
        if 'email' not in profile_data or not profile_data['email']:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400
            
        # Create the profile using DatabaseProfileManager
        profile_manager = DatabaseProfileManager()
        profile = profile_manager.create_profile(
            name=profile_data['name'],
            email=profile_data['email']
        )
        
        # Store additional fields in the profile
        for key, value in profile_data.items():
            if key not in ['name', 'email'] and value:
                profile[key] = value
                
        # Save the updated profile
        profile_manager.save_profile(profile)
        
        # Set the profile ID in the session
        session['profile_id'] = profile['id']
        
        # Return success response
        return jsonify({
            'success': True,
            'id': profile['id'],
            'message': 'Profile created successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error creating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"Error creating profile: {str(e)}"
        }), 500

@app.route('/questions')
def questions():
    """Render the questions page"""
    # Get profile_id from URL parameter or session
    profile_id = request.args.get('profile_id') or session.get('profile_id')
    
    # If profile_id is provided in URL, store it in session
    if request.args.get('profile_id'):
        session['profile_id'] = profile_id
    
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    # Initialize dependencies for the QuestionService
    from models.question_repository import QuestionRepository
    from models.database_profile_manager import DatabaseProfileManager
    
    # Initialize needed services with required dependencies
    question_repository = QuestionRepository()
    profile_manager = DatabaseProfileManager()
    question_service = QuestionService(question_repository, profile_manager)
    
    # Get next question and profile completion
    try:
        next_question, profile = question_service.get_next_question(profile_id)
    except Exception as e:
        app.logger.error(f"Error getting next question: {str(e)}")
        next_question = None
        profile = None
    
    # Ensure next_question has expected attributes if it's not None
    if next_question is not None:
        # Make sure category exists
        if 'category' not in next_question:
            next_question['category'] = 'general'
        
        # Make sure type exists
        if 'type' not in next_question:
            next_question['type'] = 'core'
            
        # Make sure is_dynamic exists
        if 'is_dynamic' not in next_question:
            next_question['is_dynamic'] = False
    
    # Get completion data
    try:
        raw_completion = question_service.get_profile_completion(profile)
    except Exception as e:
        app.logger.error(f"Error getting profile completion: {str(e)}")
        raw_completion = {
            'overall': 0,
            'core': {'overall': 0, 'count': 0, 'total': 0},
            'next_level': {'overall': 0, 'count': 0, 'total': 10},
            'behavioral': {'overall': 0, 'count': 0, 'total': 7}
        }
    
    # Format completion data for the template
    completion = {
        'overall': raw_completion.get('overall', 0),
        'by_category': {
            'demographics': 0,
            'financial_basics': 0,
            'assets_and_debts': 0,
            'special_cases': 0
        },
        'core': raw_completion.get('core', {'overall': 0}),
        'next_level': {
            'completion': raw_completion.get('next_level', {}).get('overall', 0),
            'questions_answered': raw_completion.get('next_level', {}).get('count', 0),
            'questions_count': raw_completion.get('next_level', {}).get('total', 10)
        },
        'behavioral': {
            'completion': raw_completion.get('behavioral', {}).get('overall', 0),
            'questions_answered': raw_completion.get('behavioral', {}).get('count', 0),
            'questions_count': raw_completion.get('behavioral', {}).get('total', 7)
        }
    }
    
    # Check if answered_questions method exists
    if hasattr(question_service, 'get_answered_questions'):
        answered_questions = question_service.get_answered_questions(profile_id)
    else:
        # Fallback - get answers from profile directly
        # Format the answers to match the expected template format
        answered_questions = []
        if profile and 'answers' in profile:
            for answer in profile.get('answers', []):
                # Extract question_id and answer value
                q_id = answer.get('question_id', '')
                answer_value = answer.get('answer', '')
                
                # Create a formatted QA pair object
                answered_questions.append({
                    'question': {
                        'id': q_id,
                        'text': f"Question #{len(answered_questions) + 1}",
                        'category': q_id.split('_')[0] if '_' in q_id else 'general',
                        'input_type': 'text',
                        'is_dynamic': q_id.startswith('gen_question_')
                    },
                    'answer': answer_value
                })
    
    return render_template(
        'questions.html',
        profile_id=profile_id,
        next_question=next_question,
        no_questions=next_question is None,
        completion=completion,
        answered_questions=answered_questions
    )

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit an answer to a question"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    # Get form data
    question_id = request.form.get('question_id')
    input_type = request.form.get('input_type')
    
    # Handle different input types
    if input_type == 'multiselect':
        answer = request.form.getlist('answer')
    else:
        answer = request.form.get('answer')
    
    # Initialize dependencies for the QuestionService
    from models.question_repository import QuestionRepository
    from models.database_profile_manager import DatabaseProfileManager
    
    # Initialize the service with required dependencies
    question_repository = QuestionRepository()
    profile_manager = DatabaseProfileManager()
    question_service = QuestionService(question_repository, profile_manager)
    
    # Debug information
    app.logger.info(f"Submitting answer for question ID: {question_id}, input type: {input_type}")
    app.logger.info(f"Answer value: {answer}")
    
    # Save the answer
    answer_data = {
        'question_id': question_id,
        'answer': answer,
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Save the answer and check if it was successful
        success = question_service.save_question_answer(profile_id, answer_data)
        
        if not success:
            app.logger.error(f"Failed to save answer for question {question_id} in profile {profile_id}")
            flash("There was an error saving your answer. Please try again.", "error")
    except Exception as e:
        app.logger.error(f"Exception saving answer: {str(e)}")
        flash(f"Error: {str(e)}", "error")
    
    # Return JSON response for API clients, or redirect for regular form submissions
    if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept') == 'application/json':
        # Return JSON response for AJAX submissions
        return jsonify({
            'success': True, 
            'next_url': url_for('questions', profile_id=profile_id)
        })
    else:
        # Redirect back to questions page for regular form submissions
        return redirect(url_for('questions', profile_id=profile_id))

@app.route('/switch_profile')
def switch_profile():
    """Switch to a different profile or create a new one"""
    # Clear current profile from session
    if 'profile_id' in session:
        session.pop('profile_id')
    
    # Get profile manager
    profile_manager = DatabaseProfileManager()
    
    # Get all profiles
    profiles = profile_manager.get_all_profiles()
    
    # Render template with profiles
    return render_template('switch_profile.html', profiles=profiles)

@app.route('/list_goals')
def list_goals():
    """Render the goals listing page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    # Get goals for this profile
    goal_service = app.config.get('goal_service', GoalService())
    try:
        goals = goal_service.get_goals_for_profile(profile_id)
    except AttributeError as e:
        app.logger.error(f"Error calling get_goals_for_profile: {str(e)}")
        # Fallback to get_profile_goals if it exists
        try:
            if hasattr(goal_service, 'get_profile_goals'):
                goals = goal_service.get_profile_goals(profile_id)
            else:
                # Final fallback - use direct database access
                goal_manager = GoalManager()
                goal_objects = goal_manager.get_profile_goals(profile_id)
                goals = [goal.to_dict() for goal in goal_objects] if goal_objects else []
                app.logger.info(f"Used GoalManager fallback to get {len(goals)} goals")
        except Exception as inner_e:
            app.logger.error(f"Error in fallback method: {str(inner_e)}")
            goals = []
    except Exception as e:
        app.logger.error(f"Error getting goals for profile {profile_id}: {str(e)}")
        goals = []
    
    return render_template('goals_display.html', goals=goals, profile_id=profile_id)

@app.route('/profile_complete')
def profile_complete():
    """Render the profile complete page"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    # Get profile manager
    profile_manager = DatabaseProfileManager()
    
    # Get profile
    profile = profile_manager.get_profile(profile_id)
    if not profile:
        flash("Profile not found. Please create a new profile.", "error")
        return redirect(url_for('create_profile'))
    
    # Get question service to calculate completion metrics
    # Initialize dependencies for the QuestionService
    from models.question_repository import QuestionRepository
    from services.question_service import QuestionService
    
    question_repository = QuestionRepository()
    question_service = QuestionService(question_repository, profile_manager)
    
    # Calculate completion metrics
    completion = question_service.get_profile_completion(profile)
    
    # Add by_category attribute needed for the template
    completion['by_category'] = {
        'demographics': question_repository.get_category_completion(profile, 'demographics'),
        'financial_basics': question_repository.get_category_completion(profile, 'financial_basics'),
        'assets_and_debts': question_repository.get_category_completion(profile, 'assets_and_debts'),
        'special_cases': question_repository.get_category_completion(profile, 'special_cases')
    }
    
    # Get a list of answered questions with their text
    answers = profile.get('answers', [])
    answered_questions = []
    
    # Helper function to format answers
    def _format_answer_value(value):
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        elif value is None:
            return "Not provided"
        return str(value)
    
    for answer in answers:
        q_id = answer.get('question_id', '')
        # Get question details from repository
        question = question_repository.get_question_by_id(q_id)
        if question:
            answered_questions.append({
                'question': question,
                'answer': _format_answer_value(answer.get('answer'))
            })
    
    # Render template with profile, completion metrics and answers
    return render_template('profile_complete.html', 
                          profile=profile, 
                          completion=completion,
                          answered_questions=answered_questions)

# Goal-related routes
@app.route('/create_goal', methods=['GET', 'POST'])
@app.route('/create_goal/<goal_type>', methods=['GET', 'POST'])
def create_goal(goal_type=None):
    """Create a new goal"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    goal_service = app.config.get('goal_service', GoalService())
    
    if request.method == 'POST':
        # Process the form data
        goal_data = request.form.to_dict()
        goal_data['profile_id'] = profile_id
        goal_data['user_profile_id'] = profile_id  # Ensure both profile_id and user_profile_id are set
        
        # Log form data for debugging
        app.logger.info(f"Creating goal with data: {goal_data}")
        
        # Validate required fields
        required_fields = ['category', 'title', 'target_amount', 'timeframe']
        missing_fields = [field for field in required_fields if not goal_data.get(field)]
        
        if missing_fields:
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
        
        # Validate numeric fields
        try:
            if 'target_amount' in goal_data:
                goal_data['target_amount'] = float(goal_data['target_amount'])
            if 'current_amount' in goal_data:
                goal_data['current_amount'] = float(goal_data['current_amount'])
        except ValueError:
            flash('Amount fields must be valid numbers', 'error')
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
        
        # Create the goal
        try:
            goal = goal_service.create_goal(goal_data, profile_id)
            
            # Log success details for debugging
            goal_id = goal.id if hasattr(goal, 'id') else goal.get('id')
            app.logger.info(f"Successfully created goal with ID: {goal_id}")
            
            # Calculate goal probability immediately after creation if possible
            try:
                if hasattr(goal_service, 'calculate_goal_probability'):
                    probability_result = goal_service.calculate_goal_probability(goal_id, {})
                    app.logger.info(f"Initial goal probability calculated: {probability_result}")
            except Exception as prob_error:
                app.logger.warning(f"Initial probability calculation failed: {str(prob_error)}")
            
            # Redirect to the goals list
            flash('Goal created successfully!', 'success')
            return redirect(url_for('list_goals'))
            
        except ValueError as e:
            # Handle validation errors
            error_message = str(e)
            app.logger.error(f"Validation error in create_goal: {error_message}")
            flash(f'Validation error: {error_message}', 'error')
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
            
        except TypeError as e:
            # Handle type errors
            error_message = str(e)
            app.logger.error(f"Type error in create_goal: {error_message}")
            flash(f'Field type error: {error_message}', 'error')
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
            
        except RuntimeError as e:
            # Handle database and other runtime errors
            error_message = str(e)
            app.logger.error(f"Runtime error in create_goal: {error_message}")
            flash(f'Database error: {error_message}', 'error')
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
            
        except Exception as e:
            # Handle any other unexpected errors
            error_message = str(e)
            app.logger.error(f"Unexpected error in create_goal: {error_message}", exc_info=True)
            
            # Provide more user-friendly error messages
            if "database" in error_message.lower() or "sql" in error_message.lower():
                flash('Database error occurred while saving the goal', 'error')
            elif "category" in error_message.lower():
                flash(f'Invalid goal category: {error_message}', 'error')
            else:
                flash(f'Error creating goal: {error_message}', 'error')
            
            return render_template('goal_form.html', goal_type=goal_type, action='create', goal=goal_data)
    
    # Render the goal creation form
    return render_template('goal_form.html', goal_type=goal_type, action='create', goal=None)

@app.route('/api/v2/debug/goals')
def debug_goals_list():
    """Debug endpoint to list all goals with probability information"""
    try:
        profile_id = request.args.get('profile_id')
        if not profile_id:
            return jsonify({
                'error': 'Missing profile_id parameter',
                'message': 'Please provide a profile_id query parameter'
            }), 400
            
        # Get goal service
        goal_service = app.config.get('goal_service', GoalService())
        
        # Get all goals for the profile
        goals = goal_service.get_profile_goals(profile_id, legacy_mode=False, include_probability_details=True)
        
        # Extract probability information for each goal
        probability_info = []
        for goal in goals:
            goal_info = {
                'goal_id': goal.get('id'),
                'goal_title': goal.get('title', 'Unknown'),
                'goal_category': goal.get('category', 'Unknown'),
                'goal_success_probability': goal.get('goal_success_probability'),
                'goal_success_probability_type': type(goal.get('goal_success_probability')).__name__,
                'has_probability': 'goal_success_probability' in goal,
                'has_probability_not_none': goal.get('goal_success_probability') is not None
            }
            probability_info.append(goal_info)
        
        return jsonify(probability_info)
    except Exception as e:
        app.logger.error(f"Error in debug_goals_list: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/v2/debug/recalculate/<goal_id>', methods=['POST'])
def debug_recalculate_probability(goal_id):
    """Debug endpoint to force recalculation of a goal's probability"""
    try:
        # Get services
        goal_service = app.config.get('goal_service', GoalService())
        goal_probability_analyzer = app.config.get('goal_probability_analyzer', GoalProbabilityAnalyzer())
        
        # Get the goal
        goal = goal_service.get_goal(goal_id, legacy_mode=False, include_probability_details=True)
        if not goal:
            return jsonify({
                'error': 'Goal not found',
                'goal_id': goal_id
            }), 404
            
        # Recalculate probability manually
        before_value = goal.get('goal_success_probability')
        try:
            # For debugging purposes, set a fixed probability value first
            # This is just for testing whether the UI display issue is in the calculation or display
            fixed_probability = 10.0
            app.logger.info(f"Setting fixed probability {fixed_probability} for goal {goal_id}")
            
            # Update with fixed value
            update_result = goal_service.update_goal_probability(goal_id, fixed_probability)
            
            # Log the update result
            app.logger.info(f"Fixed probability update result: {update_result}")
            
            # Add detailed tracing for debugging
            app.logger.info(f"Original goal data: {goal}")
            
            # Log stack trace for additional context
            app.logger.info(f"Stack trace for debugging:\n{traceback.format_stack()}")
            
            return jsonify({
                'goal_id': goal_id,
                'before_probability': before_value,
                'after_probability': fixed_probability,
                'calculation_success': True,
                'update_result': update_result,
                'calculation_time': datetime.now().isoformat()
            })
        except Exception as calc_error:
            app.logger.error(f"Error recalculating probability: {str(calc_error)}", exc_info=True)
            return jsonify({
                'goal_id': goal_id,
                'before_probability': before_value,
                'calculation_success': False,
                'error': str(calc_error),
                'traceback': traceback.format_exc()
            }), 500
            
    except Exception as e:
        app.logger.error(f"Error in debug_recalculate_probability: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'goal_id': goal_id,
            'traceback': traceback.format_exc()
        }), 500

@app.route('/check_probability/<goal_id>')
def check_probability(goal_id):
    """Debug route to check probability display for a specific goal"""
    goal_service = app.config.get('goal_service', GoalService())
    goal = goal_service.get_goal(goal_id)
    if not goal:
        return "Goal not found", 404
    
    # Log detailed info for debugging
    app.logger.info(f"Checking probability for goal {goal_id}:")
    app.logger.info(f"Goal data: {goal}")
    app.logger.info(f"Goal probability value: {goal.get('goal_success_probability')}")
    app.logger.info(f"Goal probability type: {type(goal.get('goal_success_probability'))}")
    return render_template('check_probability.html', goal=goal)

@app.route('/update_probability/<goal_id>', methods=['POST'])
def update_probability(goal_id):
    """Update a goal's probability for testing display"""
    try:
        goal_service = app.config.get('goal_service', GoalService())
        new_prob = request.form.get('new_prob')
        
        # Convert to float and validate
        try:
            new_prob_value = float(new_prob)
        except (ValueError, TypeError):
            return "Invalid probability value", 400
        
        # Log the update attempt
        app.logger.info(f"Attempting to update goal {goal_id} probability to {new_prob_value}")
        
        # Get the current goal first
        goal = goal_service.get_goal(goal_id)
        if not goal:
            return "Goal not found", 404
            
        app.logger.info(f"Current goal probability: {goal.get('goal_success_probability')}")
            
        # Update the probability directly in the goal object using manager
        # This is a more direct approach for testing
        try:
            goal_manager = app.config.get('goal_manager', GoalManager())
            db_goal = goal_manager.get_goal(goal_id)
            
            if db_goal:
                app.logger.info(f"Got DB goal: {db_goal.id}, current prob: {db_goal.goal_success_probability}")
                db_goal.goal_success_probability = new_prob_value
                updated = goal_manager.update_goal(db_goal)
                app.logger.info(f"Direct update result: {updated}")
                
                # Verify the update with a fresh fetch
                fresh_goal = goal_manager.get_goal(goal_id)
                app.logger.info(f"Verification - new probability: {fresh_goal.goal_success_probability}")
                
                return redirect(url_for('check_probability', goal_id=goal_id))
            else:
                return "Goal not found in manager", 404
        except Exception as db_error:
            app.logger.error(f"Error directly updating goal: {str(db_error)}", exc_info=True)
            return f"Database error: {str(db_error)}", 500
            
    except Exception as e:
        app.logger.error(f"Error in update_probability: {str(e)}", exc_info=True)
        return f"Error: {str(e)}", 500


@app.route('/edit_goal/<goal_id>', methods=['GET', 'POST'])
def edit_goal(goal_id):
    """Edit an existing goal"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect(url_for('create_profile'))
    
    goal_service = app.config.get('goal_service', GoalService())
    
    # Get the goal
    try:
        goal = goal_service.get_goal(goal_id)
        if not goal:
            flash('Goal not found!', 'error')
            return redirect(url_for('list_goals'))
    except Exception as e:
        app.logger.error(f"Error retrieving goal {goal_id}: {str(e)}")
        flash(f'Error retrieving goal: {str(e)}', 'error')
        return redirect(url_for('list_goals'))
    
    if request.method == 'POST':
        # Process the form data
        goal_data = request.form.to_dict()
        goal_data['profile_id'] = profile_id
        goal_data['goal_id'] = goal_id
        
        # Log form data for debugging
        app.logger.info(f"Updating goal {goal_id} with data: {goal_data}")
        
        # Validate required fields
        required_fields = ['category', 'title', 'target_amount', 'timeframe']
        missing_fields = [field for field in required_fields if not goal_data.get(field)]
        
        if missing_fields:
            flash(f'Missing required fields: {", ".join(missing_fields)}', 'error')
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
        
        # Validate numeric fields
        try:
            if 'target_amount' in goal_data:
                goal_data['target_amount'] = float(goal_data['target_amount'])
            if 'current_amount' in goal_data:
                goal_data['current_amount'] = float(goal_data['current_amount'])
        except ValueError:
            flash('Amount fields must be valid numbers', 'error')
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
        
        # Update the goal
        try:
            result = goal_service.update_goal(goal_id, goal_data)
            # Redirect to the goals list
            flash('Goal updated successfully!', 'success')
            
        except ValueError as e:
            # Handle validation errors
            error_message = str(e)
            app.logger.error(f"Validation error in edit_goal: {error_message}")
            flash(f'Validation error: {error_message}', 'error')
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
            
        except TypeError as e:
            # Handle type errors
            error_message = str(e)
            app.logger.error(f"Type error in edit_goal: {error_message}")
            flash(f'Field type error: {error_message}', 'error')
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
            
        except RuntimeError as e:
            # Handle database and other runtime errors
            error_message = str(e)
            app.logger.error(f"Runtime error in edit_goal: {error_message}")
            flash(f'Database error: {error_message}', 'error')
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
            
        except Exception as e:
            # Handle any other unexpected errors
            error_message = str(e)
            app.logger.error(f"Unexpected error in edit_goal: {error_message}", exc_info=True)
            
            # Provide more user-friendly error messages
            if "database" in error_message.lower() or "sql" in error_message.lower():
                flash('Database error occurred while updating the goal', 'error')
            elif "category" in error_message.lower():
                flash(f'Invalid goal category: {error_message}', 'error')
            else:
                flash(f'Error updating goal: {error_message}', 'error')
                
            return render_template('goal_form.html', goal=goal_data, action='edit', goal_type=goal.get('category', ''))
        
        return redirect(url_for('list_goals'))
    
    # Render the goal edit form
    return render_template('goal_form.html', goal=goal, action='edit', goal_type=goal.get('category', ''))

# Test route for profile creation and question flow
@app.route('/api/v2/test/profile_question_flow')
def test_profile_question_flow():
    """
    Test route that automatically tests the profile creation and question flow.
    This helps diagnose issues with the profile creation and question answer flow.
    """
    app.logger.info("Starting profile creation and question flow test")
    results = {
        'profile_creation': {'status': 'not_tested', 'details': {}},
        'question_flow': {'status': 'not_tested', 'details': {}},
        'answer_submission': {'status': 'not_tested', 'details': {}}
    }
    
    try:
        # Step 1: Test profile creation
        profile_manager = DatabaseProfileManager()
        
        # Create a test profile
        test_name = f"Test User {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_email = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        
        profile = profile_manager.create_profile(
            name=test_name,
            email=test_email
        )
        
        # Add some test data
        profile['age'] = '35'
        profile['income'] = '75000'
        profile_manager.save_profile(profile)
        
        # Record successful profile creation
        profile_id = profile['id']
        results['profile_creation'] = {
            'status': 'success',
            'details': {
                'profile_id': profile_id,
                'name': test_name,
                'email': test_email,
                'created_at': datetime.now().isoformat()
            }
        }
        
        # Step 2: Test question flow
        try:
            # Initialize QuestionService with proper dependencies
            question_repository = QuestionRepository()
            question_service = QuestionService(question_repository, profile_manager)
            
            # Get the next question for the profile
            next_question, profile = question_service.get_next_question(profile_id)
            
            if next_question:
                question_details = {
                    'id': next_question.get('id', 'unknown'),
                    'text': next_question.get('text', 'No question text'),
                    'category': next_question.get('category', 'unknown'),
                    'type': next_question.get('type', 'unknown'),
                    'input_type': next_question.get('input_type', 'text')
                }
                
                # Get completion data
                try:
                    completion = question_service.get_profile_completion(profile)
                    question_details['completion'] = completion
                except Exception as e:
                    question_details['completion_error'] = str(e)
                
                results['question_flow'] = {
                    'status': 'success',
                    'details': question_details
                }
                
                # Step 3: Test answer submission
                try:
                    # Generate a test answer based on input_type
                    input_type = next_question.get('input_type', 'text')
                    question_id = next_question.get('id')
                    
                    if input_type in ['number', 'text', 'currency']:
                        test_answer = "42"
                    elif input_type == 'select':
                        # Try to get an option from the question
                        options = next_question.get('options', [])
                        test_answer = options[0] if options else "Yes"
                    elif input_type == 'multiselect':
                        options = next_question.get('options', [])
                        test_answer = [options[0]] if options else ["Option1"]
                    elif input_type == 'date':
                        test_answer = datetime.now().strftime('%Y-%m-%d')
                    else:
                        test_answer = "Test answer"
                    
                    # Submit the answer
                    answer_data = {
                        'question_id': question_id,
                        'answer': test_answer,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    question_service.save_question_answer(profile_id, answer_data)
                    
                    # Verify the answer was saved
                    updated_profile = profile_manager.get_profile(profile_id)
                    answers = updated_profile.get('answers', [])
                    
                    # Find our answer in the profile
                    answer_found = False
                    for answer in answers:
                        if answer.get('question_id') == question_id:
                            answer_found = True
                            break
                    
                    if answer_found:
                        results['answer_submission'] = {
                            'status': 'success',
                            'details': {
                                'question_id': question_id,
                                'answer': test_answer,
                                'answer_count': len(answers)
                            }
                        }
                    else:
                        results['answer_submission'] = {
                            'status': 'error',
                            'details': {
                                'error': 'Answer not found in profile after saving',
                                'question_id': question_id,
                                'answer_submitted': test_answer,
                                'answers_in_profile': len(answers)
                            }
                        }
                
                except Exception as e:
                    app.logger.error(f"Error in answer submission test: {str(e)}")
                    results['answer_submission'] = {
                        'status': 'error',
                        'details': {'error': str(e)}
                    }
            else:
                results['question_flow'] = {
                    'status': 'error',
                    'details': {'error': 'No questions available'}
                }
        
        except Exception as e:
            app.logger.error(f"Error in question flow test: {str(e)}")
            results['question_flow'] = {
                'status': 'error',
                'details': {'error': str(e)}
            }
    
    except Exception as e:
        app.logger.error(f"Error in profile creation test: {str(e)}")
        results['profile_creation'] = {
            'status': 'error',
            'details': {'error': str(e)}
        }
    
    # Return the test results as JSON
    return jsonify({
        'test_results': results,
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'profile_creation': results['profile_creation']['status'],
            'question_flow': results['question_flow']['status'],
            'answer_submission': results['answer_submission']['status']
        }
    })

@app.route('/api/v2/test/goal_management_flow')
def test_goal_management_flow():
    """
    Test route that automatically tests the goal creation, retrieval, update, and listing flow.
    This helps diagnose issues with the goal management flow.
    """
    app.logger.info("Starting goal management flow test")
    results = {
        'profile_creation': {'status': 'not_tested', 'details': {}},
        'goal_creation': {'status': 'not_tested', 'details': {}},
        'goal_retrieval': {'status': 'not_tested', 'details': {}},
        'goal_update': {'status': 'not_tested', 'details': {}},
        'goal_listing': {'status': 'not_tested', 'details': {}}
    }
    
    try:
        # Step 1: Create a test profile for goal management testing
        profile_manager = DatabaseProfileManager()
        
        # Create a test profile
        test_name = f"Goal Test User {datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_email = f"goal_test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        
        profile = profile_manager.create_profile(
            name=test_name,
            email=test_email
        )
        
        # Record successful profile creation
        profile_id = profile['id']
        results['profile_creation'] = {
            'status': 'success',
            'details': {
                'profile_id': profile_id,
                'name': test_name,
                'email': test_email
            }
        }
        
        # Step 2: Test goal creation
        goal_service = app.config.get('goal_service', GoalService())
        
        try:
            # Create test goal data
            test_goal_data = {
                'name': 'Test Retirement Goal',
                'category': 'retirement',
                'target_amount': 1000000,
                'current_amount': 50000,
                'timeframe': (datetime.now().year + 20),
                'importance': 'high',
                'user_profile_id': profile_id,
                'notes': 'This is a test goal created by automated testing'
            }
            
            # Create the goal
            try:
                goal = goal_service.create_goal(test_goal_data, profile_id)
                if goal:
                    goal_id = goal.id if hasattr(goal, 'id') else goal.get('id')
                    
                    results['goal_creation'] = {
                        'status': 'success',
                        'details': {
                            'goal_id': goal_id,
                            'name': test_goal_data['name'],
                            'category': test_goal_data['category']
                        }
                    }
                    
                    # Step 3: Test goal retrieval
                    try:
                        retrieved_goal = goal_service.get_goal(goal_id)
                        
                        if retrieved_goal:
                            results['goal_retrieval'] = {
                                'status': 'success',
                                'details': {
                                    'goal_id': goal_id,
                                    'name': retrieved_goal.get('name'),
                                    'matches_created': retrieved_goal.get('name') == test_goal_data['name']
                                }
                            }
                            
                            # Step 4: Test goal update
                            try:
                                # Modify the goal
                                update_data = {
                                    'name': 'Updated Test Goal',
                                    'target_amount': 1200000,
                                    'notes': 'This goal was updated during testing'
                                }
                                
                                # Update the goal
                                update_result = goal_service.update_goal(goal_id, update_data)
                                
                                if update_result:
                                    # Retrieve the updated goal to verify changes
                                    updated_goal = goal_service.get_goal(goal_id)
                                    
                                    results['goal_update'] = {
                                        'status': 'success',
                                        'details': {
                                            'goal_id': goal_id,
                                            'updated_name': updated_goal.get('name'),
                                            'name_updated_correctly': updated_goal.get('name') == 'Updated Test Goal',
                                            'amount_updated_correctly': updated_goal.get('target_amount') == 1200000 or updated_goal.get('target_amount') == '1200000'
                                        }
                                    }
                                else:
                                    results['goal_update'] = {
                                        'status': 'error',
                                        'details': {
                                            'error': 'Goal update call returned False or None',
                                            'goal_id': goal_id
                                        }
                                    }
                            except Exception as e:
                                app.logger.error(f"Error in goal update test: {str(e)}")
                                results['goal_update'] = {
                                    'status': 'error',
                                    'details': {'error': str(e)}
                                }
                        else:
                            results['goal_retrieval'] = {
                                'status': 'error',
                                'details': {
                                    'error': 'Goal retrieval returned None',
                                    'goal_id': goal_id
                                }
                            }
                    except Exception as e:
                        app.logger.error(f"Error in goal retrieval test: {str(e)}")
                        results['goal_retrieval'] = {
                            'status': 'error',
                            'details': {'error': str(e)}
                        }
                else:
                    results['goal_creation'] = {
                        'status': 'error',
                        'details': {
                            'error': 'Goal creation returned None',
                            'data': test_goal_data
                        }
                    }
            except Exception as e:
                app.logger.error(f"Error in goal creation: {str(e)}")
                results['goal_creation'] = {
                    'status': 'error',
                    'details': {'error': str(e)}
                }
                
            # Step 5: Test goal listing
            try:
                # Get all goals for the profile
                goals = None
                
                try:
                    # Try the primary method
                    goals = goal_service.get_goals_for_profile(profile_id)
                except AttributeError:
                    # Try the fallback method
                    try:
                        goals = goal_service.get_profile_goals(profile_id)
                    except Exception as inner_e:
                        app.logger.error(f"Error in fallback method: {str(inner_e)}")
                        # Try direct database access
                        from models.goal_models import GoalManager
                        goal_manager = GoalManager()
                        goal_objects = goal_manager.get_profile_goals(profile_id)
                        goals = [goal.to_dict() for goal in goal_objects] if goal_objects else []
                
                if goals is not None:
                    results['goal_listing'] = {
                        'status': 'success',
                        'details': {
                            'goal_count': len(goals),
                            'goals_found': len(goals) > 0,
                            'first_goal_name': goals[0].get('name') if goals else None
                        }
                    }
                else:
                    results['goal_listing'] = {
                        'status': 'error',
                        'details': {
                            'error': 'Goal listing returned None',
                            'profile_id': profile_id
                        }
                    }
            except Exception as e:
                app.logger.error(f"Error in goal listing test: {str(e)}")
                results['goal_listing'] = {
                    'status': 'error',
                    'details': {'error': str(e)}
                }
                
        except Exception as e:
            app.logger.error(f"Error in goal management tests: {str(e)}")
            # Set any untested steps to error state
            for key in results:
                if results[key]['status'] == 'not_tested':
                    results[key] = {
                        'status': 'error',
                        'details': {'error': f'Test not run due to earlier failure: {str(e)}'}
                    }
    
    except Exception as e:
        app.logger.error(f"Error in profile creation for goal test: {str(e)}")
        results['profile_creation'] = {
            'status': 'error',
            'details': {'error': str(e)}
        }
        # Set all goal tests to error state as they depend on profile creation
        for key in results:
            if key != 'profile_creation' and results[key]['status'] == 'not_tested':
                results[key] = {
                    'status': 'error',
                    'details': {'error': 'Test not run due to profile creation failure'}
                }
    
    # Return the test results as JSON
    return jsonify({
        'test_results': results,
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'profile_creation': results['profile_creation']['status'],
            'goal_creation': results['goal_creation']['status'],
            'goal_retrieval': results['goal_retrieval']['status'],
            'goal_update': results['goal_update']['status'],
            'goal_listing': results['goal_listing']['status'],
            'overall': 'success' if all(results[key]['status'] == 'success' for key in results) else 'error'
        }
    })

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Render the login page or process login"""
    # Check if already in DEV_MODE
    dev_mode = getattr(Config, 'DEV_MODE', False)
    
    # For GET requests, just render the login page
    if request.method == 'GET':
        return render_template('login.html', dev_mode=dev_mode)
    
    # For POST requests, handle login (used for API login)
    username = request.json.get('username', '')
    password = request.json.get('password', '')
    remember = request.json.get('remember', False)
    
    # Check credentials
    if dev_mode:
        return jsonify({
            'success': True,
            'user': 'admin',
            'message': 'Logged in (DEV_MODE)',
            'token': base64.b64encode(b'admin:admin').decode('utf-8')
        })
    
    # Production mode authentication
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        # Create token
        token = base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
        
        return jsonify({
            'success': True,
            'user': username,
            'message': 'Logged in successfully',
            'token': token
        })
    
    # Invalid credentials
    return jsonify({
        'success': False,
        'message': 'Invalid credentials'
    }), 401

@app.route('/goals/delete/<goal_id>', methods=['POST', 'DELETE'])
def delete_goal(goal_id):
    """Delete a goal"""
    profile_id = session.get('profile_id')
    if not profile_id:
        return jsonify({'success': False, 'error': 'No active profile'}), 401
    
    goal_service = app.config.get('goal_service', GoalService())
    
    try:
        # Delete the goal
        result = goal_service.delete_goal(goal_id)
        if result:
            return jsonify({'success': True, 'message': 'Goal deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete goal'}), 500
    except Exception as e:
        app.logger.error(f"Error deleting goal {goal_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Handle logout"""
    # Client-side logout handled by JavaScript
    # Just render a simple confirmation page
    return render_template('logout.html')

# Admin routes
@app.route('/admin/')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html')

@app.route('/admin/profiles')
@admin_required
def admin_profiles():
    """Admin profiles page"""
    profile_manager = DatabaseProfileManager()
    profiles = profile_manager.get_all_profiles()
    return render_template('admin/profiles.html', profiles=profiles)

@app.route('/admin/profiles/<profile_id>')
@admin_required
def admin_profile_detail(profile_id):
    """Admin profile detail page"""
    profile_manager = DatabaseProfileManager()
    try:
        profile = profile_manager.get_profile(profile_id)
    except Exception as e:
        app.logger.error(f"Error getting profile {profile_id}: {str(e)}")
        flash(f'Error retrieving profile: {str(e)}', 'error')
        return redirect(url_for('admin_profiles'))
    
    if not profile:
        flash('Profile not found!', 'error')
        return redirect(url_for('admin_profiles'))
    
    goal_service = app.config.get('goal_service', GoalService())
    try:
        goals = goal_service.get_goals_for_profile(profile_id)
    except AttributeError as e:
        app.logger.error(f"Error calling get_goals_for_profile: {str(e)}")
        # Fallback to get_profile_goals if it exists
        try:
            if hasattr(goal_service, 'get_profile_goals'):
                goals = goal_service.get_profile_goals(profile_id)
            else:
                # Final fallback - use direct database access
                goal_manager = GoalManager()
                goal_objects = goal_manager.get_profile_goals(profile_id)
                goals = [goal.to_dict() for goal in goal_objects] if goal_objects else []
                app.logger.info(f"Used GoalManager fallback to get {len(goals)} goals")
        except Exception as inner_e:
            app.logger.error(f"Error in fallback method: {str(inner_e)}")
            goals = []
    except Exception as e:
        app.logger.error(f"Error getting goals for profile {profile_id}: {str(e)}")
        goals = []
    
    return render_template('admin/profile_detail.html', profile=profile, goals=goals)

@app.route('/admin/insights')
@admin_required
def admin_insights():
    """Admin insights page"""
    return render_template('admin/insights.html')

@app.route('/admin/metrics')
@admin_required
def admin_metrics():
    """Admin metrics page"""
    return render_template('admin/metrics.html')

@app.route('/admin/parameters')
@admin_required
def admin_parameters():
    """Admin parameters page"""
    # Get the parameter service
    param_service = get_financial_parameter_service()
    
    # Get all parameters
    parameters = param_service.get_all_parameters()
    
    return render_template('admin/parameters.html', parameters=parameters)

@app.route('/admin/cache')
@admin_required
def admin_cache():
    """Admin cache management page"""
    # Get cache stats if the cache is initialized
    try:
        from models.monte_carlo.cache import get_cache_stats
        cache_stats = get_cache_stats()
    except:
        cache_stats = {'error': 'Cache system not initialized'}
    
    return render_template('admin/cache.html', cache_stats=cache_stats)

@app.route('/profile_analytics', defaults={'profile_id': None})
@app.route('/profile_analytics/<profile_id>')
def view_profile_analytics(profile_id):
    """View analytics for a profile"""
    # Check if profile ID provided or use from session
    if not profile_id and 'profile_id' in session:
        profile_id = session['profile_id']
    
    if not profile_id:
        flash('No profile ID provided', 'error')
        return redirect(url_for('index'))

    # Get the profile
    profile_manager = DatabaseProfileManager()
    profile = profile_manager.get_profile(profile_id)
    
    if not profile:
        flash('Profile not found!', 'error')
        return redirect(url_for('index'))
    
    # Set the profile in the session
    session['profile_id'] = profile_id
    
    try:
        # Get the analytics service, passing the required profile_manager
        analytics_service = ProfileAnalyticsService(profile_manager)
        
        # Get analytics data
        analytics_data = analytics_service.generate_profile_analytics(profile_id)
        
        if not analytics_data:
            app.logger.error(f"No analytics data generated for profile {profile_id}")
            analytics_data = {
                "error": "Failed to generate analytics data",
                "profile_id": profile_id,
                "profile_name": profile.get("name", "Unknown"),
                "generated_at": datetime.now().isoformat()
            }
        elif 'error' in analytics_data:
            app.logger.warning(f"Analytics service returned error: {analytics_data['error']}")
            # The service already provides default data structure with the error
        
        # Log the data for debugging
        app.logger.info(f"Generated analytics data for profile {profile_id}: {str(analytics_data.keys() if analytics_data else 'None')}")
        
        return render_template('profile_analytics.html', 
                            profile=profile, 
                            profile_id=profile_id,
                            analytics=analytics_data)
                            
    except Exception as e:
        app.logger.error(f"Exception in profile_analytics route: {str(e)}")
        # Provide a minimal analytics data structure with the error
        analytics_data = {
            "error": f"Failed to process analytics data: {str(e)}",
            "profile_id": profile_id,
            "profile_name": profile.get("name", "Unknown"),
            "generated_at": datetime.now().isoformat(),
            "dimensions": {},
            "investment_profile": {
                "type": "Error",
                "description": "An error occurred while generating analytics",
                "allocation": {}
            }
        }
        
        return render_template('profile_analytics.html', 
                            profile=profile, 
                            profile_id=profile_id,
                            analytics=analytics_data)

# Add this at the bottom of your app.py file
if __name__ == '__main__':
    print("Starting Flask app on alternative port...")
    app.run(debug=True, host='0.0.0.0', port=5432)  # Use a different port
