from argparse import ArgumentParser
from setuptools import setup
import sys

parser = ArgumentParser(add_help=False)
parser.add_argument("-c", "--camera", help="Type of camera",
                    type=str.lower,
                    required=False,
                    default="webcam",
                    choices=["webcam", "basler", "digitalcam", "picam"])
addition_args = ['-c', '--camera']
addition_args += ["webcam", "basler", "digitalcam", "picam"]
args, _ = parser.parse_known_args()
install_requires = [
    "aiohttp",
    "attrs",
    "influxdb-client",
    "numpy",
    "opencv-python-headless",
    "requests"
]

camera_args = args.camera.lower()
if args.camera == "basler":
    install_requires.append("pypylon")
elif args.camera == "digitalcam":
    install_requires.append("gphoto2")
elif args.camera == "picam":
    install_requires.append("picamera")

# Remove  additional args
for i in range(len(sys.argv)):
    if sys.argv[i].lower() in addition_args:
        sys.argv[i] = sys.argv[i].lower()

arg_list = sys.argv.copy()
for arg in arg_list:
    if arg in addition_args:
        sys.argv.remove(arg)

setup(
    name='timelapse',
    version='0.1',
    packages=[
        'server', 'client'
    ],
    package_date={'resource':['resources']},
    include_pacakge_data=True,
    install_requires=install_requires,
    zip_safe=False
)
