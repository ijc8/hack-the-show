import asyncio
import json

import mido
from sanic import Sanic

app = Sanic("WebsocketExample")
output = mido.open_output("HackTheShow", virtual=True)

# TODO: Replace with actual parameters.
PARAMS = list("ABCDEFGH")
MIN_VALUE = 0
MAX_VALUE = 127

state = {p: 0 for p in PARAMS}
update = asyncio.Event()

@app.websocket("/ws")
async def websocket(request, ws):
    # A coroutine is spawned for each connected client.
    global state
    client_state = state.copy()
    print("New websocket connection from", request.ip)
    # New connection: send the current state.
    await ws.send(json.dumps(state))
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
                    state[param] = max(MIN_VALUE, min(state[param] + delta, MAX_VALUE))
                    output.send(mido.Message(type='control_change', channel=0, control=PARAMS.index(param), value=state[param]))
                    # Clients update their local state immediately:
                    client_state[param] += delta
                # Signal to all coroutines that they should send updates to their clients.
                update.set()
                update.clear()
                recv = asyncio.create_task(ws.recv())
            elif task is updated:
                # State updated.
                # Compute the diff with the client's local state, and send the necessary updates.
                diff = {k: v for k, v in state.items() if v != client_state[k]}
                # Don't send a message if nothing needs to be updated.  
                if diff:
                    client_state.update(state)
                    await ws.send(json.dumps(diff))
                updated = asyncio.create_task(update.wait())

app.static("/", "index.html")
app.static("/test", "test.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
