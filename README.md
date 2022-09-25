# interactive-concert

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

Go to http://0.0.0.0:8000 to use the client. Go to http://0.0.0.0:8000/test for basic stress-testing.

The server creates two virtual MIDI devices: an input and an output named "HackTheShow".

Whenever anyone changes a slider, the server sends a CC message to the output on channel 11-13 (depending on the mode) for control 1-8 (depending on the slider) with the new slider value.

When the server receives a CC message for control 1-3, it changes the mode accordingly.
