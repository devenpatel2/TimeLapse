
import asyncio
from base64 import b64decode
from datetime import datetime
import json
import logging
import os
import struct
import typing as T

from aiohttp import web, MultipartReader
import cv2
import numpy as  np

from influx_handler import InfluxHandler

logging.basicConfig()
logger = logging.getLogger("server")
logger.setLevel(logging.INFO)

routes = web.RouteTableDef()


PATH = "data"

now = lambda : datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
class Record:
    def __init__(self):
        self._image = None
        self._timestamp = None
        self._filename = None
        self._weather = None
      

    @property
    def image(self):
        return self._image
        
    @image.setter
    def image(self, val: str):
        buf = val.encode('utf-8')
        val = b64decode(buf)
        self._image = val
    
    @property
    def timestamp(self):
        return self._timestamp
    
    @timestamp.setter
    def timestamp(self, val: int):
        self._timestamp = val
    
    @property
    def filename(self):
        return self._filename


    @filename.setter
    def filename(self, val: str):
        full_path = os.path.realpath(PATH)
        val = os.path.join(full_path, val)
        self._filename = val


    @property
    def weather(self):
        return self._weather

    
    @weather.setter
    def weather(self, val: T.Dict):
        self._weather = val

    @property
    def data (self):
        influx_body = {"measurement": "image_data",
            "tags": {
                "location" : "balcony"
            },
            "time": now(),
            "fields": {
                "image" : self.filename,
                "temperature" : self.weather['temperature'],
                "wind_speed": self.weather['wind']
            }
        }
        return influx_body


    def __str__(self):
        return (f"{self.filename}, "
                f"{self.timestamp}, "
                f"{self.weather}")

'''
@routes.post('/api/files')
async def post_files(request):

        
    reader = MultipartReader.from_response(request)
    record = Record()
    influx_handler = app['influx_handler']
    while True:
        
        
        part = await reader.next()
        if part is None:
            break
        try:
            val = await part.text()
            setattr(record, part.filename, val)
        except Exception:
            print(f"Failed for reading {part.filename} attribute")
            logger.warning("failed to read data", exc_info=True)
            cont = await part.read()
            print(cont)

        
    logger.info(record)
    
    if record.filename and record.image:
        with open(record.filename, 'wb') as f:
            f.write(record.image)
    influx_handler.post(record.data)
    return web.json_response({"status": "Success", "status_code": 200}, status=200)
'''

@routes.post('/api/data')
async def post_data(request):

    #influx_handler = app['influx_handler']
    record = Record()

    data = await request.text()
    data = json.loads(data)

    for key, val in data.items():
        try:
            setattr(record, key, val)
        except Exception:
            logger.error(f"failed to set attr {key}", exc_info=True)

    
    if record.filename and record.image:
        with open(record.filename, 'wb') as f:
            f.write(record.image)
    
        with InfluxHandler() as influx_handler:   
            influx_handler.post('test_bucket', record.data)

    else:
        return web.json_response(
            {"status": "Failed to write image", "status_code": 500}, status=500)

    return web.json_response({"status": "Success", "status_code": 200}, status=200)

if __name__ == "__main__":
    
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    app = web.Application()
    app.add_routes(routes)
    app['influx_handler'] = InfluxHandler()
    web.run_app(app, port=8080)
