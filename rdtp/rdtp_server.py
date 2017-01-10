import SocketServer
import rdtp_common
import Queue

class MachineHandler(SocketServer.BaseRequestHandler):
    """
    Subclass of SocketServer. In proper usage, one only overwrites
    self.handle(). This is a TCP server for the listening portion
    of the machine. Therefore, we are using this on the server.
    """
    def handle(self):
        """
        Continually fetch new messages and add them to our Queue.
        Messages should come in the following format:
            "[remote_pid]:[message]"

        Currently, does not support the use of colons inside the message body.
        """
        while True:
            try:
                status, args = rdtp_common.recv(self.request)
            except rdtp_common.ClientDead:
                continue
             
            assert(status == 0)
            print args, " got args"
            assert(len(args) == 2)

            remote_pid, message = args[0], args[1]
            self.server.queue.put((remote_pid, message))

class Server():
    """
    Wrapper for the TCP server.
    Holds incoming messages in a synchronized queue that can be
    used in both MachineHandler's `handle` and the main program
    logic.
    """
    def __init__(self, host, port):
        self.listener = SocketServer.TCPServer((host, port), MachineHandler, False)
        self.listener.allow_reuse_address = True
        self.listener.server_bind()
        self.listener.server_activate()

        # Create a synchronized queue
        self.queue = Queue.Queue()
        self.listener.queue = self.queue

    def serve_forever(self):
        self.listener.serve_forever()


