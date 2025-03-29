# debug_server.py
from flask import Flask, request, jsonify, send_from_directory
import os
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Debug middleware to trace all requests
@app.before_request
def log_request_info():
    logger.debug('Request Headers: %s', dict(request.headers))
    logger.debug('Request Path: %s', request.path)
    logger.debug('Request Method: %s', request.method)
    logger.debug('Request Remote Address: %s', request.remote_addr)

# Simple index route
@app.route('/')
def index():
    return "Debug server is running"

# Test static file route
@app.route('/static/<path:filename>')
def serve_static(filename):
    logger.debug("Attempting to serve static file: %s", filename)
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
    logger.debug("Static folder path: %s", static_folder)
    return send_from_directory(static_folder, filename)

# Debug info endpoint
@app.route('/debug-info')
def debug_info():
    return jsonify({
        'environment': dict(os.environ),
        'flask_config': {k: str(v) for k, v in app.config.items()},
        'request_headers': dict(request.headers)
    })

if __name__ == '__main__':
    # Create a simple static test file if it doesn't exist
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    os.makedirs(static_dir, exist_ok=True)

    test_file_path = os.path.join(static_dir, 'test.html')
    if not os.path.exists(test_file_path):
        with open(test_file_path, 'w') as f:
            f.write("<html><body><h1>Test Static File</h1></body></html>")

    logger.info("Starting debug server...")
    logger.info("Created test file at: %s", test_file_path)
    app.run(debug=True, port=5001)
