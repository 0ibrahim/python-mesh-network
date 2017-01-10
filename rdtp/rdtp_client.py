import socket
import select
import rdtp_common
import os
from time import sleep

host_pid = os.getpid()

class Client():
    """
    Client which does all the sending for
    the application.
    """
    def __init__(self, host, port):
        """
        Create a client with some host and port.
        """
        self.host = host
        self.port = int(port)

    def __str__(self):
        return self.host + ':' + str(self.port)

    def connect(self):
        """
        Continually tries opening a socket on the provided
        port. Retries every time unit until succeeding.
        """
        while True:
            try:
                print "connecting"
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.connect((self.host, self.port))

                break
            except:
                sleep(1)

    def send(self, message):
        """
        Sends a message to the connected server.
        """
        rdtp_common.send(self.socket, 0, str(host_pid), str(message))
