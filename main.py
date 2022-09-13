import asyncio
from sanic import Sanic

app = Sanic("WebsocketExample")

counter = 0
update = asyncio.Event()

@app.websocket("/ws")
async def websocket(request, ws):
    # A coroutine is spawned for each connected client.
    global counter
    print("New websocket connection from", request.ip)
    # New connection: send the current value of the counter.
    await ws.send(str(counter))
    recv = asyncio.create_task(ws.recv())
    updated = asyncio.create_task(update.wait())
    while True:
        # Wait for a new message from our client, or an update to the counter (from another client).
        # Handle whichever happens first.
        done, _ = await asyncio.wait({recv, updated}, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            if task is recv:
                # Uncomment to see what we got from the client:
                # message = task.result()
                # print(f"Got message from {request.ip}: {message}")
                # Got a message from the client; increment the counter.
                counter += 1
                # Signal to all coroutines that they should send updates to their clients.
                update.set()
                update.clear()
                recv = asyncio.create_task(ws.recv())
            elif task is updated:
                # Counter updated: send the new value to our client.
                await ws.send(str(counter))
                updated = asyncio.create_task(update.wait())

app.static("/", "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
