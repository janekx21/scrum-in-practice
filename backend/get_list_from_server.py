import asyncio
import websockets
import os
import struct

URI = "ws://141.44.17.48:8768"

# Wenn True: Datei enthält [u32_len][payload...]
# Wenn False: Datei enthält nur payload (exakt so wie vom WebSocket geliefert)
WRITE_LENGTH_PREFIX = False

async def get_streams_async():

    async with websockets.connect(URI, max_size=None) as ws:
        await ws.send("list")
        response = await ws.recv()
        print("Available datasets:", response)

    return response.split(",")
       
def get_streams() -> list[str]:
    return asyncio.run(get_streams_async())

