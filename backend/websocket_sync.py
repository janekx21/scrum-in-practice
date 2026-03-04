import asyncio
import websockets
import os
import struct

URI = "ws://141.44.17.48:8768"

# Wenn True: Datei enthält [u32_len][payload...]
# Wenn False: Datei enthält nur payload (exakt so wie vom WebSocket geliefert)
WRITE_LENGTH_PREFIX = False

async def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(base_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    frame_counter = 0

    async with websockets.connect(URI, max_size=None) as ws:
        await ws.send("list")
        response = await ws.recv()
        print("Available datasets:", response)

        dataset = response.split(",")[1].strip()
        await ws.send(f"start:{dataset}")
        print(f"Started dataset: {dataset}")

        while True:
            message = await ws.recv()

            if isinstance(message, (bytes, bytearray, memoryview)):
                payload = bytes(message)  # komplette WS-Binary-Message

                print("Received binary frame:", len(payload), "bytes")

                filename = os.path.join(temp_dir, f"frame_{frame_counter:06d}.bin")
                with open(filename, "wb") as f:
                    if WRITE_LENGTH_PREFIX:
                        f.write(struct.pack("<I", len(payload)))
                    f.write(payload)

                frame_counter += 1
            else:
                print("Text message:", message)

asyncio.run(main())