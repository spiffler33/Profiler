import sys
import webbrowser
import time

if len(sys.argv) < 2:
    print("Usage: python debug_browser.py <goal_id>")
    sys.exit(1)
    
goal_id = sys.argv[1]
url = f"http://127.0.0.1:5000/check_probability/{goal_id}"
print(f"Opening browser to: {url}")
webbrowser.open(url)
