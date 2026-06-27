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
    while True:
        stats = websocket.app.state.metrics.get_stats()
        await websocket.send_text(json.dumps(stats))
        await asyncio.sleep(1)