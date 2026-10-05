import asyncio
import websockets

async def test_ws(path):
    url = f"ws://127.0.0.1:8000{path}"
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as ws:
            print("Connected!")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    await test_ws("/ws/garbage")

if __name__ == "__main__":
    asyncio.run(main())
