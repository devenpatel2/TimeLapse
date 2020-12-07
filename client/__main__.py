#!/usr/bin/env python
from argparse import ArgumentParser
from base64 import b64encode
from datetime import datetime
from functools import partial
import io
import logging
import os
import socket
import struct
import typing as T
import time

import cv2
import numpy as np
import requests

import camera
from camera import Camera
from utils import ShutdownHandler

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

Path = T.Union[str, os.PathLike]

api_route = "/api/data"
server_port = 8080

HEADERS = {'content-type': 'multipart/form-data; '
           'boundary=my-boundary'}
HEADERS = {'content-type': 'application/json'}
LAT = 48.107580
LONG = 11.509070
WEATHER_API = "79072d2ce0e828772115aa080119dac8"
URL = ("http://api.openweathermap.org/data/2.5/weather?"
       f"lat={LAT}&lon={LONG}&appid={WEATHER_API}")


def float2byte(x): return bytearray(struct.pack("f", x))


def get_weather_data():
    res = requests.get(URL)
    data = res.json()
    temp = round(data['main']['temp'] - 273, 2)
    temp = 0.88
    wind = round(data['wind']['speed'], 2)
    print(temp, wind)
    return {'temperature': temp, 'wind': wind}


def get_post_data(image: np.ndarray) -> T.Dict:
    now_ts = time.time()
    now_human_readable = datetime.fromtimestamp(
        now_ts).strftime('%Y_%m_%d_%H_%M_%S')
    image_name = f"{now_human_readable}.jpg"
    buffer = cv2.imencode('.jpg', image)[1]
    b64_image = b64encode(buffer)
    # print(type(b64_image))
    data = {'image': b64_image.decode('utf-8'),
            'filename': image_name,
            'timestamp': int(now_ts * 1000)}
    data['weather'] = get_weather_data()
    # for key, val in get_weather_data().items():
    #    data.update({key:float2byte(val)})

    return data


def post_image(url: Path, image: np.ndarray) -> bool:

    url = f"http://{url}:{server_port}{api_route}"
    data = get_post_data(image)
    logger.info(f"posting image to {url}")
    res = requests.post(url, json=data, headers=HEADERS)
    if res.status_code == 200:
        return True
    return False


def save_image(path: Path, image: np.ndarray) -> bool:
    now = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    filename = os.path.join(path, f"{now}.jpg")
    logger.info(f"savng image to {filename}")
    status = cv2.imwrite(filename, image)
    return status


def is_ip(path: str) -> bool:
    try:
        socket.inet_aton(path)
        return True
    except OSError:
        return False


def capture_image(
    cam: Camera,
    save_func: T.Callable[[np.ndarray], bool]
) -> None:

    image = cam.capture()
    try:
        status = save_func(image)
        if not status:
            logger.warning("Failed to post/save image")
    except Exception:
        logger.error("Failed to save image", exc_info=True)


def main(args):
    shutdown_handler = ShutdownHandler()
    cam = getattr(camera, args.camera)()

    if is_ip(args.output):
        save_func = partial(post_image, args.output)
    else:
        if not os.path.exists(args.output):
            os.makedirs(args.output)
        save_func = partial(save_image, args.output)

    try:
        while True:
            if shutdown_handler.shutdown:
                break
            capture_image(cam, save_func)
            time.sleep(args.time)
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt. Exiting..")


if __name__ == "__main__":

    parser = ArgumentParser(description="Timelapse Camera")
    parser.add_argument("-c", "--camera", required=True, help="Type of camera",
                        choices=["WebCam", "Basler", "DigitalCam"])
    parser.add_argument("-t", "--time", required=True,
                        type=int, help="Time interval for capture")
    parser.add_argument("-o", "--output", required=True,
                        help="Path/URL to save/upload images")
    args = parser.parse_args()

    main(args)
