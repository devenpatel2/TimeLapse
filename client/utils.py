import signal

class ShutdownHandler(object):

    shutdown = False

    def __init__(self):

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.shutdown = True