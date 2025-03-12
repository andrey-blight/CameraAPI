import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from camera_parser import parse
from models import AlertModel
from telegram import Bot
from telegram.error import TelegramError

TELEGRAM_API_TOKEN = '7678648058:AAFOWIHyEpQArJb12nbEXL6Zuc2IXC_rCb8'
CHAT_ID = '-1002499876267'

last_send = None


async def send_telegram_message(message: str):
    global last_send
    try:
        now_time = datetime.now()
        if last_send is None or now_time - last_send > timedelta(seconds=2):
            last_send = now_time
            await bot.send_message(chat_id=CHAT_ID, text=message)
    except TelegramError as e:
        print(f"error while send, {e}")


# Инициализация бота
bot = Bot(token=TELEGRAM_API_TOKEN)
CAMERAS = parse()


# Start saving stream
@asynccontextmanager
async def lifespan(f_app: FastAPI):

    yield

    for i, camera in CAMERAS.items():
        camera.stop()
    print("End of lifespan")


app = FastAPI(lifespan=lifespan)
app.mount("/hls", StaticFiles(directory="hls"), name="hls")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/start/{cam_id}")
async def start(cam_id: int):
    if cam_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    CAMERAS[cam_id].start()
    return "OK"


@app.post("/stop/{cam_id}")
async def stop(cam_id: int):
    if cam_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    CAMERAS[cam_id].stop()
    return 'OK'


@app.get("/hls/{cam_id}/stream.m3u8")
async def stream_camera(cam_id: int):
    """Get camera stream by id"""

    if cam_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    camera = CAMERAS[cam_id]
    return camera.stream_response()


@app.get("/cam")
async def get_cameras_list():
    return {cam_id: str(cam) for cam_id, cam in CAMERAS.items()}


@app.get("/cam/story/{cam_id}")
async def get_camera_story(cam_id: int):
    if cam_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    video_path = CAMERAS[cam_id].save_video()

    def iter_file(path):
        try:
            with open(path, mode="rb") as file:
                yield from file
        finally:
            os.remove(path)

    return StreamingResponse(iter_file(video_path), media_type="video/mp4")


clients = set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        clients.remove(websocket)


@app.post("/alert")
async def send_alert(body: AlertModel):
    message = {"alert": f"{body.cam_id} {body.resp_type}"}

    # await send_telegram_message(message["alert"])

    for client in clients:
        await client.send_json(message)

    return {"status": "alert sent"}
