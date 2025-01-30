import cv2
import asyncio
from collections import deque
from fastapi.responses import StreamingResponse
import time


class RTSPCamera:
    def __init__(self, rtsp_url: str, fps: int = 10, buffer_seconds: int = 5):
        """
        Init camera

        :param rtsp_url: camera's URL RTSP
        :param fps: speed of camera (default: 10)
        :param buffer_seconds: time for buffering (default: 5)
        """
        self.rtsp_url = rtsp_url
        self.fps = fps
        self.buffer_size = fps * buffer_seconds  # max size of frames
        self.interval = 1 / fps  # time to sleep for frame waiting
        self.frames = deque(maxlen=self.buffer_size)  # Deque for frame storage
        self.running = False  # Flag for starting save stream
        self.lock = asyncio.Lock()  # lock for synchronization

    async def start(self):
        """Start frame storaging"""
        self.running = True
        asyncio.create_task(self._capture_frames())

    async def stop(self):
        """Stop frame storaging"""
        self.running = False

    async def _capture_frames(self):
        """Асинхронная задача для захвата кадров."""
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            print(f"Can't open camera stream {self.rtsp_url}")
            return

        while self.running:
            start_time = time.time()
            ret, frame = cap.read()
            if ret:
                async with self.lock:
                    self.frames.append(frame)

            # Wait until next frame
            elapsed = time.time() - start_time
            await asyncio.sleep(max(0.0, self.interval - elapsed))

        cap.release()

    async def get_last_video(self) -> bytes:
        """
        Get last video frame duration buffer_seconds
        :return: Video bytes
        """
        async with self.lock:
            if not self.frames:
                raise ValueError("No frames available")
            frames_copy = list(self.frames)

        height, width, _ = frames_copy[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = "/tmp/last_5_seconds.mp4"
        out = cv2.VideoWriter(video_path, fourcc, self.fps, (width, height))

        for frame in frames_copy:
            out.write(frame)
        out.release()

        with open(video_path, "rb") as video_file:
            video_bytes = video_file.read()

        return video_bytes

    async def stream_response(self):
        """
        Get stream
        :return: StreamingResponse
        """

        async def video_stream():
            cap = cv2.VideoCapture(self.rtsp_url)
            if not cap.isOpened():
                print(f"Can't load camera {self.rtsp_url}")
                return

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
                await asyncio.sleep(1 / self.fps)

            cap.release()

        return StreamingResponse(video_stream(),
                                 media_type="multipart/x-mixed-replace; boundary=frame")
