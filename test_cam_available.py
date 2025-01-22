import cv2
from time import sleep


def main(rtsp_url):
    # Open the RTSP stream
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print("Error: Could not open video stream.")
        return

    while True:
        # Read a frame from the stream
        ret, frame = cap.read()
        frame = cv2.resize(frame, (1920 // 2, 1080 // 2))

        if not ret:
            print("Error: Could not read frame.")
            break

        # Display the frame
        cv2.imshow('RTSP Stream', frame)
        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the video capture object and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    rtsp_url = "rtsp://test:test@87.229.255.237:554/0"  # Replace with your RTSP URL
    main(rtsp_url)
