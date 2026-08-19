from fastapi import FastAPI, WebSocket
from fastapi.responses import FileResponse
import asyncio
import json

app = FastAPI()

@app.get("/")
def serve_dashboard():
    return FileResponse("Dashboard/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async def send_stats():
        while True:
            stats = websocket.app.state.metrics.get_stats()
            await websocket.send_text(json.dumps(stats))
            await asyncio.sleep(1)

    async def receive_messages():
        while True:
            if await websocket.receive_text() == "Toggle_Peak":
                websocket.app.state.sim_state.is_peak = not websocket.app.state.sim_state.is_peak

    await asyncio.gather(send_stats(), receive_messages())
