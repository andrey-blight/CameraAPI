import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from camera_functions import get_video_stream, start_camera_processing


# Фоновая задача для запуска камер
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(start_camera_processing(CAMERA_IPS))

    yield

    print("End of lifespan")


app = FastAPI(lifespan=lifespan)
CAMERA_IPS = {
    1: "rtsp://test:test@87.229.255.237:554/0",
    2: "rtsp://test:test@87.229.255.237:554/0",
    3: "rtsp://test:test@87.229.255.237:554/0",
}

@app.get("/cam/{cam_id}")
async def stream_camera(cam_id: int):
    """Эндпоинт для стрима видео с камеры по cam_id."""

    if cam_id not in CAMERA_IPS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    rtsp_url = CAMERA_IPS[cam_id]
    return StreamingResponse(get_video_stream(rtsp_url),
                             media_type="multipart/x-mixed-replace; boundary=frame")


@app.get("/cam")
async def get_cameras_list():
    return CAMERA_IPS


@app.get("/cam/story/{cam_id}")
async def get_camera_story(cam_id: int):
    pass
