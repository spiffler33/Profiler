"""
Direct WSGI server runner for authentication testing.
"""

import os
import sys
from werkzeug.serving import run_simple
from app import app

# Configure for development
os.environ['FLASK_ENV'] = 'development'
os.environ['DEV_MODE'] = 'True'
os.environ['FLASK_DEBUG'] = '1'

if __name__ == '__main__':
    # Print configuration
    print(f"DEV_MODE: {os.environ.get('DEV_MODE')}")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    print(f"FLASK_DEBUG: {os.environ.get('FLASK_DEBUG')}")
    
    # Manually configure app
    app.config['DEV_MODE'] = True
    app.config['DEBUG'] = True
    
    # Run the app directly
    run_simple('localhost', 5000, app, use_reloader=True, use_debugger=True)