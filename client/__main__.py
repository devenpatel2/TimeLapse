#!/usr/bin/env python
import asyncio
from argparse import ArgumentParser
from functools import partial
import logging
import os
import time

from . import camera
from . import client_helpers as ch
from .mjpeg_server import MjpegServer

logging.basicConfig()
logger = logging.getLogger('client')
logger.setLevel(logging.INFO)


def run(args):

    if ch.is_ip(args.output):
        save_func = partial(ch.post_image, args.output)
    else:
        if not os.path.exists(args.output):
            os.makedirs(args.output)
        save_func = partial(ch.save_image, args.output)

    while True:
        with getattr(camera, args.camera)() as cam:
            ch.capture_image(cam, save_func)
        time.sleep(args.time)


def stream(args):

    print(args)
    cam = getattr(camera, args.camera)()
    mjpeg = MjpegServer(port=args.port)
    mjpeg.add_stream('stream', cam.capture)

    try:
        asyncio.run(mjpeg.start())
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Closing Stream")
    finally:
        cam.close()
        asyncio.run(mjpeg.stop())


if __name__ == "__main__":

    parser = ArgumentParser(description="Timelapse Camera")
    sub_parsers = parser.add_subparsers(
        help='run <cmd> --help for subcommand  options')

    run_parser = sub_parsers.add_parser('run', help='start application')
    run_parser.add_argument("-c", "--camera", help="Type of camera",
                            default="WebCam",
                            choices=["WebCam", "Basler", "DigitalCam"])
    run_parser.add_argument("-t", "--time", required=True,
                            type=int, help="Time interval for capture")
    run_parser.add_argument("-o", "--output", required=True,
                            help="Path/URL to save/upload images")
    run_parser.set_defaults(func=run)

    stream_parser = sub_parsers.add_parser('stream', help='start mjpeg stream')
    stream_parser.add_argument(
        '-p', '--port', type=str, default='8000', help='Mjpeg steam port')
    stream_parser.add_argument("-c", "--camera", help="Type of camera",
                               default="WebCam",
                               choices=["WebCam", "Basler", "DigitalCam"])
    stream_parser.set_defaults(func=stream)

    parser.prog = "client"
    run_parser.prog = f"{parser.prog} run"
    stream_parser.prog = f"{parser.prog} stream"
    args = parser.parse_args()

    try:
        args.func(args)
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt. Exiting..")
