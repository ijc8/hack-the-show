# minimal-websocket-example

Minimal example showing how to share some state between many clients with WebSockets.

This demonstrates the minimal parts needed for this kind of thing:
- A client (HTML + JavaScript)
- A server (in this case, Python, but there are lots of options)

Setup:
```bash
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

Execution:
```bash
python main.py
```

Then go to http://0.0.0.0:8000 and click the button. Try opening multiple browsers, or connecting from another device.
