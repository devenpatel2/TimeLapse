import asyncio
from functools import partial
import logging
import os

from aiohttp import web, MultipartWriter
import cv2
logging.basicConfig()
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("mjpeg-server")
log_level = getattr(logging, log_level)
logger.setLevel(log_level)


async def mjpeg_stream(get_frame, request):
    my_boundary = 'image-boundary'
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'multipart/x-mixed-replace;boundary={}'.format(my_boundary)
        }
    )
    await response.prepare(request)
    while True:
        try:
            frame = get_frame()
        except Exception:
            logger.error("Failed to get frame", exc_info=True)
            break

        if frame is None:
            logger.warning("No frame recieved, exiting...")
            break
        jpeg_frame = cv2.imencode('.jpg', frame)[1]
        frame_bytes = jpeg_frame.tobytes()

        with MultipartWriter('image/jpeg', boundary=my_boundary) as mpwriter:
            mpwriter.append(frame_bytes, {
                'Content-Type': 'image/jpeg'
            })
            try:
                await mpwriter.write(response, close_boundary=False)
            except ConnectionResetError:
                logger.warning("Client connection closed")
                break
        await response.write(b"\r\n")


class MjpegServer:

    def __init__(self, host='0.0.0.0', port="8080"):
        self._port = port
        self._host = host
        self._app = web.Application()
        self._cam_routes = []
        self._runner = None
        self._event = None

    async def root_handler(self, request):  # pylint: disable=unused-argument
        # TO-DO : load page with links
        text = 'Available streams:\n\n'
        for route in self._cam_routes:
            text += f"{route} \n"
        return web.Response(text=text)

    async def start(self):
        self._event = asyncio.Event()
        self._app.router.add_route("GET", "/", self.root_handler)
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        site = web.TCPSite(
            self._runner, host=self._host, port=self._port, shutdown_timeout=2)
        await site.start()
        logger.info((f"{'='*10}Server running on "
                     f"{self._host}:{self._port}"
                     f"{'='*10}"))
        await self._event.wait()
        await self._stop()

    def add_stream(self, route, func):
        route = f"/{route}"
        self._cam_routes.append(route)
        stream_handler = partial(mjpeg_stream, func)
        self._app.router.add_route("GET", f"{route}", stream_handler)

    async def _stop(self):
        await asyncio.sleep(0.1)
        await self._app.shutdown()
        await self._runner.cleanup()

    async def stop(self):
        if self._event:
            logger.warning("stopping server")
            self._event.set()
        await asyncio.sleep(0.1)
