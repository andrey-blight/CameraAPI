import os
import signal
import subprocess
import shutil
import threading
import glob
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
        if self.running:
            return
        self.running = True
        self.start_ffmpeg()

    def stop(self):
        """Stop frame storaging"""
        self.running = False
        if self.process is not None:
            self.process.send_signal(signal.SIGTERM)
            self.process.wait()
            self.process = None
            try:
                shutil.rmtree(f"hls/{self.cam_id}")
            except Exception:
                print("No dir")

    def start_ffmpeg(self):
        """Запускает ffmpeg для указанной камеры"""
        output_dir = f"hls/{self.cam_id}"
        os.makedirs(output_dir, exist_ok=True)

        command = [
            "ffmpeg",
            "-rtsp_transport", "tcp",  # 🔹 TCP для стабильности (по умолчанию UDP)
            "-i", self.rtsp_url,

            # 🔹 Декодирование
            "-fflags", "nobuffer",  # Убираем буферизацию
            "-flags", "+global_header",  # Глобальные заголовки
            "-threads", "2",  # Ограничиваем потоки для стабильности

            # 🔹 Видео
            "-vf", "scale=640:360,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-tune", "zerolatency",  # 🔹 Минимальная задержка
            "-crf", "23",  # 🔹 Контроль качества (0 — макс, 51 — худшее)
            "-b:v", "800k",  # 🔹 Оптимальный битрейт
            "-maxrate", "900k",
            "-bufsize", "1200k",

            # 🔹 FPS и ключевые кадры
            "-r", "10",  # FPS = 10
            "-g", "50",  # 🔹 GOP = 10 FPS * 5 сек
            "-keyint_min", "50",  # 🔹 Ключевой кадр каждые 50 кадров

            # 🔹 Аудио (если нужно)
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
            "-ar", "44100",

            # 🔹 HLS Настройки
            "-f", "hls",
            "-hls_time", "5",  # 🔹 Длина сегмента 5 сек
            "-hls_list_size", "5",
            "-hls_flags", "delete_segments+append_list",  # 🔹 Удаляем старые, но не прерываем поток
            "-hls_segment_type", "mpegts",  # 🔹 Формат сегментов
            "-hls_allow_cache", "0",  # 🔹 Отключаем кеширование
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
            f"{output_dir}/stream.m3u8"
        ]

        self.process = subprocess.Popen(command,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                                        )

    def stream_response(self):
        return FileResponse(f"hls/{self.cam_id}/stream.m3u8",
                            headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    def get_latest_segment(self):
        """Находит последний `.ts` файл по времени изменения"""
        ts_files = glob.glob(os.path.join(f"hls/{self.cam_id}", "segment_*.ts"))
        if not ts_files:
            return None
        return max(ts_files, key=os.path.getmtime)


if __name__ == '__main__':
    cam = RTSPCamera("rtsp://itlcamview:hatp344gh@192.168.100.22:554/live/main")
    print("started")
    cam.start()
    # time.sleep(10)
    #
    # cam.save_video()
    # print("done")
