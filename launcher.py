import os
import sys

if os.environ.get('WHOCORD_PIPELINE'):
    from discord_osint.__main__ import main
    main()
    sys.exit(0)

# Normal launch – start the web dashboard
import threading
import webbrowser
import time
from web_app import app

def open_browser():
    time.sleep(1)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False)
