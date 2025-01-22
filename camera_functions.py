import cv2
import os
import time
import asyncio

FPS = 10
FRAME_INTERVAL = 1 / FPS


def get_video_stream(rtsp_url: str):
    """Генератор кадров для передачи видео потока."""
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        raise RuntimeError(f"Не удается открыть камеру по URL: {rtsp_url}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Конвертируем кадр в формат JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        # Формат отправки для x-mixed-replace
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()


async def _clean_old_files(camera_dir):
    current_time = time.time()

    for file in os.listdir(camera_dir):
        file_path = os.path.join(camera_dir, file)

        file_time = os.path.getmtime(file_path)
        if current_time - file_time > 5:  # save only last five seconds
            os.remove(file_path)


async def _process_camera(camera_url, camera_id):
    # create dir where we will save camera stream
    camera_dir = os.path.join("tmp", f"camera_{camera_id}")
    os.makedirs(camera_dir, exist_ok=True)

    cap = cv2.VideoCapture(camera_url)
    if not cap.isOpened():
        print(f"Cannot open camera id: {camera_id} rtsp: {camera_url}")
        return

    while True:
        start_time = time.time()  # save start time
        ret, frame = cap.read()
        if ret:
            # save frame
            timestamp = int(time.time() * 1000)
            frame_path = os.path.join(camera_dir, f"{timestamp}.jpg")
            cv2.imwrite(frame_path, frame)

            # Удаляем старые кадры
            await _clean_old_files(camera_dir)

        # Ждем до следующего кадра
        elapsed = time.time() - start_time
        await asyncio.sleep(max(0., FRAME_INTERVAL - elapsed))


# Запуск обработки камер
async def start_camera_processing(camera_urls: dict):
    tasks = []
    for cam_id, rtsp in camera_urls.items():
        tasks.append(_process_camera(rtsp, str(cam_id)))
    await asyncio.gather(*tasks)
