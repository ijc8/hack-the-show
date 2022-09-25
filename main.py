import asyncio
import json
import threading

import mido
from sanic import Sanic

app = Sanic("WebsocketExample")
input = mido.open_input("HackTheShow", virtual=True)
output = mido.open_output("HackTheShow", virtual=True)

mode = 0

def process_midi():
    for message in input:
        if message.is_cc() and 1 <= message.control <= 3:
            mode = message.control - 1
            print("Mode change:", mode)

# TODO: Replace with actual parameters.
PARAMS = list("ABCDEFGH")
MIN_VALUE = 0
MAX_VALUE = 127

state = [0 for _ in PARAMS]
update = asyncio.Event()

@app.websocket("/ws")
async def websocket(request, ws):
    # A coroutine is spawned for each connected client.
    global state
    client_state = state[:]
    print("New websocket connection from", request.ip)
    # New connection: send the current state.
    await ws.send(json.dumps(list(zip(PARAMS, state))))
    recv = asyncio.create_task(ws.recv())
    updated = asyncio.create_task(update.wait())
    while True:
        # Wait for a new message from our client, or an update to the state (from another client).
        # Handle whichever happens first.
        done, _ = await asyncio.wait({recv, updated}, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task is recv:
                # Uncomment to see what we got from the client:
                message = json.loads(task.result())
                # print(f"Got message from {request.ip}: {message}")
                # Got a message from the client; update the state.
                for param, delta in message.items():
                    param = int(param)
                    state[param] = max(MIN_VALUE, min(state[param] + delta, MAX_VALUE))
                    output.send(mido.Message(type='control_change', channel=11 + mode, control=param + 1, value=state[param]))
                    # Clients update their local state immediately:
                    client_state[param] += delta
                # Signal to all coroutines that they should send updates to their clients.
                update.set()
                update.clear()
                recv = asyncio.create_task(ws.recv())
            elif task is updated:
                # State updated.
                # Compute the diff with the client's local state, and send the necessary updates.
                diff = [[i, v] for i, v in enumerate(state) if v != client_state[i]]
                # Don't send a message if nothing needs to be updated.  
                if diff:
                    client_state[:] = state
                    await ws.send(json.dumps(diff))
                updated = asyncio.create_task(update.wait())

app.static("/", "index.html")
app.static("/test", "test.html")

if __name__ == "__main__":
    t = threading.Thread(target=process_midi, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=8000)
