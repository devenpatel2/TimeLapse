from abc import ABC, abstractmethod
import os
import logging
import time

import cv2
import numpy as np

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


try:
    import gphoto2 as gp
except (ImportError, ModuleNotFoundError):
    logger.warning("Failed to import gphoto2 "
                   "Only needed for DigitalCamera")
try:
    from pypylon import pylon
except (ImportError, ModuleNotFoundError):
    logger.warning("Failed to import pypylon "
                   "Only needed for Basler Camera")

try:
    from picamera import PiCamera
    from picamera.array import PiRGBArray
except (ImportError, ModuleNotFoundError):
    logger.warning("Failed to import picamera "
                   "Only needed for Pi-Cam")


class Camera(ABC):

    def __init__(self, camera_type="generic"):
        self._camera_type = camera_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def camera_type(self):
        return self._camera_type

    @abstractmethod
    def capture(self, *kwargs):
        pass

    def start(self):
        pass

    @abstractmethod
    def close(self):
        pass

    def __repr__(self):
        return f"Camera({self._camera_type})"


class DummyCam(Camera):

    def __init__(self):
        super().__init__(camera_type="Dummy")

    def capture(self):
        rnd_image = np.random.randint(
            0, 255, [1024, 1920, 3]).astype(dtype=np.uint8)
        return rnd_image

    def close(self):
        pass


class WebCam(Camera):

    def __init__(self):
        super().__init__(camera_type="WebCam")
        self._camera = cv2.VideoCapture(0)

    def close(self):
        logger.info("closing camera")
        self._camera.release()

    def capture(self):
        ret, frame = self._camera.read()
        if not ret:
            raise Exception("Failed to capture image")
        return frame


class Basler(Camera):

    def __init__(self):
        super().__init__(camera_type="Basler")
        self._camera = pylon.InstantCamera(
            pylon.TlFactory.GetInstance().CreateFirstDevice())
        converter = pylon.ImageFormatConverter()
        # converting to opencv bgr format
        converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self._converter = converter

        self._camera.Open()
        self.configure_camera()
        self._camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

    def configure_camera(self):
        self._camera.ExposureAuto.SetValue("Continuous")

    def capture(self):
        grabResult = self._camera.RetrieveResult(
            5000, pylon.TimeoutHandling_ThrowException)
        image = self._converter.Convert(grabResult)
        grabResult.Release()
        return image.GetArray()

    def close(self):
        logger.info("closing camera")
        self._camera.Close()


class DigitalCam(Camera):

    def __init__(self):
        super().__init__(camera_type="DigitalCam")
        self._camera = gp.Camera()
        # self._camera.init()

    def close(self):
        logger.info("closing camera")
        self._camera.exit()

    # TO-DO
    # implement continous capture for streaming
    def capture(self, tmp_path="/tmp/gp2_capture"):
        if not os.path.exists(tmp_path):
            os.makedirs(tmp_path)
        file_path = self._camera.capture(gp.GP_CAPTURE_IMAGE)
        target = os.path.join(tmp_path, file_path.name)
        camera_file = self._camera.file_get(
            file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL)
        camera_file.save(target)
        image = cv2.imread(target)
        return image


class PiCam(Camera):

    def __init__(self):
        super().__init__(camera_type="PiCamera")
        self._init_camera()

    def _init_camera(self):
        self._camera = PiCamera()
        self._camera.resolution = (1280, 720)
        self._camera.start_preview()
        logger.info("Initializing PiCamera...")
        time.sleep(2)

    def stream(self):
        with PiRGBArray(self._camera) as stream:
            self._camera.capture(stream, format='bgr')
            yield stream.array.astype(np.uint8)

    def capture(self):
        with PiRGBArray(self._camera) as stream:
            self._camera.capture(stream, format='bgr')
            return stream.array

    def close(self):
        logger.info("closing camera")
        self._camera.close()


def test_driver():
    cam = Basler()
    image = cam.capture()
    # print(image.shape)
    cv2.imshow("image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cam.close()


if __name__ == "__main__":

    test_driver()
