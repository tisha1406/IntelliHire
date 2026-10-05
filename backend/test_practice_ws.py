import asyncio
import json
import websockets
from app.auth.jwt_handler import create_access_token

async def main():
    # 1. Create token for mock candidate
    candidate_id = "6a749346ba2af4d02d21e4a9"
    company_id = "6a749346ba2af4d02d21e4a1"
    
    token = create_access_token({
        "sub": "mock_user",
        "user_id": "mock_user",
        "role": "candidate",
        "candidate_id": candidate_id,
        "company_id": company_id
    }, "candidate")
    
    # 2. Get a new practice session via HTTP
    import httpx
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        resp = await client.post(
            "/api/candidate/practice/start",
            headers={"Authorization": f"Bearer {token}"}
        )
        data = resp.json()
        print("HTTP start:", data)
        session_id = data["data"]["session_id"]
        
    # 3. Connect via WS
    uri = f"ws://127.0.0.1:8000/api/ws/interview/{session_id}?token={token}"
    async with websockets.connect(uri) as ws:
        msg = await ws.recv()
        print("WS msg 1 (connection_ready):", msg)
        
        msg = await ws.recv()
        print("WS msg 2 (session_snapshot):", msg)
        
        # 4. Send start
        print("Sending start_interview")
        await ws.send(json.dumps({
            "command_type": "start_interview",
            "command_id": "cmd-123"
        }))
        
        msg = await ws.recv()
        print("WS msg 3:", msg)
        
        msg = await ws.recv()
        print("WS msg 4:", msg)
        
        msg = await ws.recv()
        print("WS msg 5:", msg)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(".env")
    asyncio.run(main())
