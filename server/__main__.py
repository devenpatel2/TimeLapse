from argparse import ArgumentParser
import os
import json
from aiohttp import web
from .server import routes

with open('resource/secret.json') as f:
    config_data = json.load(f)

config = config_data['server_config']

PATH = config["IMAGE_PATH"]
PORT = str(config["PORT"])


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', type=str,
                        default=PORT, required=False,
                        help="Server port")
    args = parser.parse_args()
    if not os.path.exists(PATH):
        os.makedirs(PATH)

    app = web.Application()
    app['data_path'] = PATH
    app.add_routes(routes)
    web.run_app(app, port=args.port)
