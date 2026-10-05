import asyncio
import websockets

async def test_ws():
    url = "ws://127.0.0.1:8000/ws/interview/123?token=abc"
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers={"Origin": "http://localhost:5173"}) as ws:
            print("Connected!")
            await ws.recv()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ws())
