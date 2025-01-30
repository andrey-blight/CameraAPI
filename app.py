import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from camera_functions import get_video_stream, start_camera_processing
from RTSPCamera import RTSPCamera

CAMERA_IPS = {
    1: "rtsp://test:test@87.229.255.237:554/0",
    2: "rtsp://test:test@87.229.255.237:554/0",
    3: "rtsp://test:test@87.229.255.237:554/0",
}
CAMERAS = {
    1: RTSPCamera("rtsp://test:test@87.229.255.237:554/0")
}


# Start saving stream
@asynccontextmanager
async def lifespan(f_app: FastAPI):
    for i, camera in CAMERAS.items():
        await camera.start()

    yield

    print("End of lifespan")


app = FastAPI(lifespan=lifespan)


@app.get("/cam/{cam_id}")
async def stream_camera(cam_id: int):
    """Get camera stream by id"""

    if cam_id not in CAMERAS:
        raise HTTPException(status_code=404, detail="Камера не найдена")

    camera = CAMERAS[cam_id]
    return camera.stream_response()


@app.get("/cam")
async def get_cameras_list():
    return CAMERA_IPS


@app.get("/cam/story/{cam_id}")
async def get_camera_story(cam_id: int):
    pass
