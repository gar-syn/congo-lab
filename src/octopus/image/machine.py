# Sibling Imports
from .data import ImageProperty

# Package Imports
from ..machine import Machine


class CameraViewer (Machine):

    protocolFactory = None
    name = "Monitor a webcam"

    update_frequency = 1

    def setup (self):
        # setup variables
        self.image = ImageProperty(title = "Image", fn = self._get_image)

    def start (self):
        self._tick(self.image.refresh, self.update_frequency)

    # def show (self):
    #     self._get_image().show()

    def _get_image (self):
        return self.protocol.image()

    def stop (self):
        self._stopTicks()

    def disconnect (self):
        self.stop()

        try:
            self.protocol.disconnect()
        except AttributeError:
            pass
