import csv

from RTSPCamera import RTSPCamera


def parse():
    cameras = {}
    with open("cameras.csv") as file:
        for i, val in enumerate(csv.reader(file)):
            if i == 0:
                continue
            host = val[0]
            cameras[i] = RTSPCamera(str(i), f"rtsp://itlcamview:hatp344gh@{host}/live/main")
    return cameras
