"""
Minimal Flask app with authentication for testing
"""

from flask import Flask, jsonify, request, Response
import base64
import uuid
from datetime import datetime
import os
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('minimal_auth.log'),
        logging.StreamHandler()
    ]
)

# Create app
app = Flask(__name__)

# Configuration
DEV_MODE = os.environ.get('DEV_MODE', 'True').lower() in ('true', '1', 't')
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

@app.route('/public', methods=['GET'])
def public_endpoint():
    """Public endpoint that requires no auth"""
    logging.info("Public endpoint accessed")
    
    return jsonify({
        'status': 'success',
        'message': 'Public endpoint accessible',
        'timestamp': datetime.now().isoformat(),
        'dev_mode': DEV_MODE
    })

@app.route('/admin', methods=['GET'])
def admin_endpoint():
    """Admin endpoint that requires auth in production"""
    logging.info(f"Admin endpoint accessed, DEV_MODE: {DEV_MODE}")
    
    # If in development mode, bypass authentication
    if DEV_MODE:
        logging.info("Authentication bypassed due to DEV_MODE")
        return jsonify({
            'status': 'success',
            'message': 'Admin endpoint accessible with DEV_MODE',
            'timestamp': datetime.now().isoformat(),
            'dev_mode': DEV_MODE
        })
    
    # Otherwise check for authorization
    auth_header = request.headers.get('Authorization', None)
    if not auth_header or not auth_header.startswith('Basic '):
        logging.warning("Missing or invalid auth header")
        return jsonify({
            'status': 'error',
            'message': 'Authentication required'
        }), 401
        
    # Decode and verify credentials
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 1)
        
        logging.info(f"Auth attempt with username: {username}")
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            logging.info("Authentication successful")
            return jsonify({
                'status': 'success',
                'message': 'Admin endpoint accessible with auth',
                'timestamp': datetime.now().isoformat(),
                'dev_mode': DEV_MODE,
                'username': username
            })
        else:
            logging.warning("Invalid credentials")
            return jsonify({
                'status': 'error',
                'message': 'Invalid credentials'
            }), 401
    except Exception as e:
        logging.error(f"Error decoding auth header: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid authorization header'
        }), 401

@app.route('/auth-debug', methods=['GET'])
def auth_debug():
    """Debug endpoint for auth information"""
    logging.info("Auth debug endpoint accessed")
    
    auth_header = request.headers.get('Authorization', 'None')
    safe_auth_header = auth_header[:10] + '...' if auth_header != 'None' and len(auth_header) > 10 else auth_header
    
    return jsonify({
        'dev_mode': DEV_MODE,
        'auth_header': safe_auth_header,
        'has_valid_format': auth_header.startswith('Basic ') if auth_header != 'None' else False,
        'timestamp': datetime.now().isoformat(),
        'environment': {
            'DEV_MODE': os.environ.get('DEV_MODE', 'Not set'),
            'FLASK_ENV': os.environ.get('FLASK_ENV', 'Not set'),
            'DEBUG': os.environ.get('FLASK_DEBUG', 'Not set')
        }
    })

if __name__ == '__main__':
    port = 5050
    logging.info(f"Starting minimal auth test app on port {port}")
    logging.info(f"DEV_MODE: {DEV_MODE}")
    app.run(debug=True, port=port)