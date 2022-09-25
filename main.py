import asyncio
import json
import threading
import time
import os

import mido
from sanic import Sanic

app = Sanic("WebsocketExample")
input = mido.open_input("HackTheShow", virtual=True)
output = mido.open_output("HackTheShow", virtual=True)

mode = 0
last_mode_switch = time.time()

def process_midi():
    global last_mode_switch
    for message in input:
        if message.is_cc() and 1 <= message.control <= 3:
            last_mode_switch = time.time()
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
                t = time.time()
                # Uncomment to see what we got from the client:
                message = json.loads(task.result())
                # print(f"Got message from {request.ip}: {message}")
                # Got a message from the client; update the state.
                for param, delta in message.items():
                    param = int(param)
                    state[param] = max(MIN_VALUE, min(state[param] + delta, MAX_VALUE))
                    output.send(mido.Message(type='control_change', channel=11 + mode, control=param + 1, value=state[param]))
                    # Log the interaction.
                    json.dump({"time": t, "mode_time": t - last_mode_switch, "mode": mode, "ip": request.ip, "param": param, "delta": delta}, log)
                    log.write("\n")
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
    os.makedirs("log", exist_ok=True)
    with open(f"log/{time.strftime('%Y_%m_%d-%H_%M_%S')}.jsonl", "w") as log:
        t = threading.Thread(target=process_midi, daemon=True)
        t.start()
        app.run(host="0.0.0.0", port=8000)
