import cv2
import ffmpeg
import hashlib
import tempfile
import time
import threading
from datetime import datetime
from collections import deque


class RTSPCamera:
    FPS = 15

    def __init__(self, rtsp_url: str, buffer_seconds: int = 5):
        """
        Init camera

        :param rtsp_url: camera's URL RTSP
        :param buffer_seconds: time for buffering (default: 5 seconds)
        """
        self.rtsp_url = rtsp_url
        self.buffer_size = self.FPS * buffer_seconds  # max size of frames
        self.frames = deque(maxlen=self.buffer_size)  # Deque for frame storage

        self.running = False  # Flag for starting save stream
        self.lock = threading.Lock()  # Lock for synchronize frames deque
        self.capture_thread = None  # Thread of capturing

    def __str__(self):
        return self.rtsp_url

    def start(self):
        """Start frame storaging"""
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.capture_thread.start()

    def stop(self):
        """Stop frame storaging"""
        self.running = False

    def _capture_frames(self):
        """Save frames in thread to self.frames."""
        cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            print(f"Can't open camera stream {self.rtsp_url}")
            return

        while self.running:

            ret, frame = cap.read()

            if ret:
                frame = cv2.resize(frame, (1920, 1080))

                with self.lock:
                    self.frames.append(frame)

        cap.release()

    def save_video(self) -> str:
        """
        Get last video frame duration buffer_seconds
        :return: Video bytes
        """
        with self.lock:
            if not self.frames:
                raise ValueError("No frames available")
            frames_copy = list(self.frames)

        with tempfile.TemporaryDirectory() as tmpdir:

            for i, frame in enumerate(frames_copy):
                frame_filename = f"{tmpdir}/frame_{i:03d}.png"
                cv2.imwrite(frame_filename, frame)

            output_video = f"tmp/{self._get_hash()}.mp4"
            ffmpeg.input(f'{tmpdir}/frame_%03d.png', framerate=15).output(output_video, vcodec='libx264',
                                                                          pix_fmt='yuv420p').run()

        return output_video

    def _get_hash(self) -> str:
        cur_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        str_to_hash = f"{cur_time}_{self.rtsp_url}"

        return hashlib.sha256(str_to_hash.encode()).hexdigest()

    #
    # async def stream_response(self):
    #     """
    #     Get stream
    #     :return: StreamingResponse
    #     """
    #
    #     async def video_stream():
    #         cap = cv2.VideoCapture(self.rtsp_url)
    #         if not cap.isOpened():
    #             print(f"Can't load camera {self.rtsp_url}")
    #             return
    #
    #         while True:
    #             ret, frame = cap.read()
    #             if not ret:
    #                 break
    #             _, buffer = cv2.imencode('.jpg', frame)
    #             frame_bytes = buffer.tobytes()
    #             yield (
    #                     b"--frame\r\n"
    #                     b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
    #             )
    #             await asyncio.sleep(1 / self.fps)
    #
    #         cap.release()
    #
    #     return StreamingResponse(video_stream(),
    #                              media_type="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    cam = RTSPCamera("rtsp://itlcamview:hatp344gh@192.168.100.22:554/live/main")
    print("started")
    cam.start()
    time.sleep(10)

    cam.save_video()
    print("done")
