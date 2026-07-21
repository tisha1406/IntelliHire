from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)


@router.websocket("/interview/{session_id}")
async def interview_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    Week 1

    WebSocket route signature only.

    Actual interview streaming logic
    will be implemented later.
    """

    await websocket.accept()

    try:
        await websocket.send_json(
            {
                "status": "connected",
                "session_id": session_id,
                "message": "WebSocket connection established."
            }
        )

        while True:
            data = await websocket.receive_text()

            await websocket.send_json(
                {
                    "received": data,
                    "status": "placeholder"
                }
            )

    except WebSocketDisconnect:
        print(f"Client disconnected from session {session_id}")