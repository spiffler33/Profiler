from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
CORS(app)

# Set up auth for comparison
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == 'admin' and password == 'admin':
        return username
    return None

@app.route('/')
def hello():
    return "Hello World"

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Add a protected route to test auth
@app.route('/protected')
@auth.login_required
def protected():
    return "This is a protected route"

if __name__ == '__main__':
    app.run(debug=True, port=5001)