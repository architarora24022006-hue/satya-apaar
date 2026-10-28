import asyncio
import json
from datetime import datetime, timezone
from typing import List, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/realtime", tags=["Realtime Alerts & WebSockets"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.add(connection)
        for dead in dead_connections:
            self.active_connections.discard(dead)

manager = ConnectionManager()

# Helper to broadcast alert to all connected dashboard clients
async def broadcast_alert(alert_type: str, title: str, description: str, severity: str = "HIGH", metadata: dict = None):
    payload = {
        "id": f"ALERT-{int(datetime.now().timestamp() * 1000)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": alert_type,
        "title": title,
        "description": description,
        "severity": severity,
        "metadata": metadata or {}
    }
    await manager.broadcast(payload)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for live dashboard telemetry and instant fraud alerts.
    Clients receive real-time push events when clashes, seat locks, or uploads occur.
    """
    await manager.connect(websocket)
    try:
        # Send initial connection handshake
        await websocket.send_json({
            "type": "HANDSHAKE_ESTABLISHED",
            "message": "Connected to SATYA-APAAR Real-time Sentinel Stream",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        while True:
            # Keep connection open and receive any client ping/filter requests
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@router.get("/sse")
async def sse_alert_stream():
    """Server-Sent Events (SSE) alternative for firewalled client environments."""
    async def event_generator():
        while True:
            await asyncio.sleep(15)
            ping_event = {
                "event": "heartbeat",
                "data": json.dumps({"status": "LIVE", "timestamp": datetime.now(timezone.utc).isoformat()})
            }
            yield f"data: {json.dumps(ping_event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
