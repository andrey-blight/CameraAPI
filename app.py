import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from RTSPCamera import RTSPCamera

CAMERAS = {
    1: RTSPCamera("rtsp://itlcamview:hatp344gh@192.168.100.22:554/live/main")
}


# Start saving stream
@asynccontextmanager
async def lifespan(f_app: FastAPI):
    for i, camera in CAMERAS.items():
        camera.start()

    yield

    for i, camera in CAMERAS.items():
        camera.stop()
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
