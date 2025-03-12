import os
import signal
import subprocess

import hashlib
import tempfile
import threading
from datetime import datetime

from fastapi.responses import FileResponse


class RTSPCamera:
    FPS = 10

    def __init__(self, cam_id: str, rtsp_url: str, buffer_seconds: int = 3):
        """
        Init camera

        :param rtsp_url: camera's URL RTSP
        :param buffer_seconds: time for buffering (default: 5 seconds)
        """
        self.cam_id = cam_id
        self.rtsp_url = rtsp_url
        self.buffer_seconds = buffer_seconds
        self.running = False
        self.lock = threading.Lock()
        self.process = None

    def __str__(self):
        return self.rtsp_url

    def start(self):
        """Start frame storaging"""
        self.running = True
        self.start_ffmpeg()

    def stop(self):
        """Stop frame storaging"""
        self.running = False
        if self.process is not None:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait()
            self.process = None

    def start_ffmpeg(self):
        """Запускает ffmpeg для указанной камеры"""
        output_dir = f"hls/{self.cam_id}"
        os.makedirs(output_dir, exist_ok=True)
        print(self.cam_id)
        command = [
            "ffmpeg",
            "-i", self.rtsp_url,  # Входной RTSP-поток

            # Видео
            "-vf", "scale=640:360,format=yuv420p",  # Масштабирование на GPU
            "-c:v", "libx264",  # Кодируем на CPU
            "-preset", "veryfast",  # Баланс скорости и качества
            "-r", "10",

            # Формат вывода (HLS)
            "-f", "hls",
            "-hls_time", "2",  # Длительность каждого сегмента (в секундах)
            "-hls_list_size", "5",  # Количество сегментов в плейлисте
            "-hls_flags", "delete_segments",  # Удаление старых сегментов
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",  # Имена сегментов
            f"{output_dir}/stream.m3u8"  # Имя плейлиста
        ]

        self.process = subprocess.Popen(command)

    def stream_response(self):
        return FileResponse(f"hls/{self.cam_id}/stream.m3u8",
                            headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


if __name__ == '__main__':
    cam = RTSPCamera("rtsp://itlcamview:hatp344gh@192.168.100.22:554/live/main")
    print("started")
    cam.start()
    # time.sleep(10)
    #
    # cam.save_video()
    # print("done")
