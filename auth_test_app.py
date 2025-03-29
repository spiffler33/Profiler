"""
Standalone minimal Flask app for authentication testing
"""

from flask import Flask, jsonify, request, Response
import base64
import os
import uuid
from datetime import datetime

# Create minimal Flask app
app = Flask(__name__)

# Set dev mode
DEV_MODE = True

@app.route('/api/public', methods=['GET'])
def public_endpoint():
    """Public endpoint that requires no auth"""
    return jsonify({
        'status': 'success',
        'message': 'Public endpoint is working',
        'timestamp': datetime.now().isoformat(),
        'request_id': str(uuid.uuid4())
    })

@app.route('/api/dev-auth', methods=['GET'])
def dev_auth_endpoint():
    """Endpoint that bypasses auth in dev mode"""
    # If DEV_MODE is enabled, always return success
    if DEV_MODE:
        return jsonify({
            'status': 'success',
            'message': 'Authentication bypassed in DEV_MODE',
            'dev_mode': DEV_MODE,
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())
        })
    
    # Otherwise check for authorization
    auth_header = request.headers.get('Authorization', None)
    if not auth_header or not auth_header.startswith('Basic '):
        return jsonify({
            'status': 'error',
            'message': 'Authentication required'
        }), 401
    
    # Decode credentials
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 1)
        
        # Very simple auth check
        if username == 'admin' and password == 'admin':
            return jsonify({
                'status': 'success',
                'message': 'Authentication successful',
                'dev_mode': DEV_MODE,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4())
            })
    except Exception as e:
        app.logger.error(f"Error decoding auth header: {str(e)}")
    
    return jsonify({
        'status': 'error',
        'message': 'Authentication failed'
    }), 401

@app.route('/api/protected', methods=['GET'])
def protected_endpoint():
    """Endpoint that requires authentication, bypassed in dev mode"""
    # Always check for authorization
    auth_header = request.headers.get('Authorization', None)
    
    # If DEV_MODE is enabled, still log but don't require auth
    if DEV_MODE:
        return jsonify({
            'status': 'success',
            'message': 'Protected endpoint accessed with DEV_MODE bypass',
            'dev_mode': DEV_MODE,
            'has_auth': bool(auth_header),
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4())
        })
    
    # In production mode, validate credentials
    if not auth_header or not auth_header.startswith('Basic '):
        return jsonify({
            'status': 'error',
            'message': 'Authentication required'
        }), 401
    
    # Decode credentials
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = auth_decoded.split(':', 1)
        
        # Simple auth check
        if username == 'admin' and password == 'admin':
            return jsonify({
                'status': 'success',
                'message': 'Authentication successful',
                'dev_mode': DEV_MODE,
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'request_id': str(uuid.uuid4())
            })
    except Exception as e:
        app.logger.error(f"Error decoding auth header: {str(e)}")
    
    return jsonify({
        'status': 'error',
        'message': 'Authentication failed'
    }), 401

if __name__ == '__main__':
    # Run app with debugging enabled
    print(f"Starting auth test app in DEV_MODE: {DEV_MODE}")
    app.run(debug=True, port=5050)