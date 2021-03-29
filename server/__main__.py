from argparse import ArgumentParser
import os

from aiohttp  import web
from .server import routes

PATH = "/mnt/data/images"


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=str,
                        default='8082', required=False,
                        help="Server port")
    args = parser.parse_args()
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    app = web.Application()
    app['data_path'] = PATH
    app.add_routes(routes)
    web.run_app(app, port=args.port)
