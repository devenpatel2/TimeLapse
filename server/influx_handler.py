from collections import namedtuple
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

TOKEN = ""
INFLUX_INFO = namedtuple("INFLUX_INFO",
                         "url, token, org")


class InfluxHandler:

    def __init__(self,
                 token: str,
                 org: str,
                 host: str = 'localhost',
                 port: int = 8086,
                 ):

        if not host.startswith("http"):
            url = f"http://{host}"

        url = f"{host}:{port}"

        self._db_info = INFLUX_INFO(url, token, org)
        self._write_api = None

    def __enter__(self):
        self._client = InfluxDBClient(
            url=self._db_info.url, token=self._db_info.token, org=self._db_info.org)

        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()

    def _init(self):
        self._client = InfluxDBClient(
            url=self._db_info.url, token=self._db_info.token, org=self._db_info.org)

        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)

    def post(self, bucket, data):
        data_point = Point.from_dict(data)
        if self._write_api is None:
            self._init()
        self._write_api.write(bucket, self._db_info.org, data_point)
