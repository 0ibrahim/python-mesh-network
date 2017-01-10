from constants import *
from rdtp.rdtp_client import Client
from rdtp.rdtp_server import Server
from clientsHolder import ClientsHolder
import thread
import sys, os
from time import strftime
import threading
from messageWrapper import wrap_message, unwrap_message, gen_uid

# Run this script with a sys argument of HOST:PORT.

COORDINATOR_HOST = "localhost"
COORDINATOR_PORT = 2000

def make_host_port(arg):
    args = arg.split(':')
    return args[0], int(args[1])

class Node:
    """
    Implements logic for the node on the mesh network.

    These nodes act independently.

    Every node has:
        - one server (for receiving)
        - n clients (one for each peer node)
        - when a node dies, kill the associated client.
        - it doesn't hurt much to keep that client around,
          so basically, if send ever fails, kill that client.

    First, you should spin up a coordinator on the
    COORDINATOR_HOST and COORDINATOR_POST
    listed above.

    Then, you should spin up the nodes in independent terminals.
    They'll be able to talk to each other!

    There are some command line arguments that will be described here later...
    """

    def __init__(self, host, port, reliability, speed):
        self.server = None
        self.host = host
        self.port = port
        self.reliability = reliability
        self.speed = speed
        self.clientsHolder = ClientsHolder()

        # hashmap for quick recall of what message uids we've encountered
        # prevents us from looking at things multiple times unnecessarily.
        self.seen = {}

    def usage(self):
        print "Usage: python node.py HOST:PORT"
        exit()

    def log_write(self, log, str):
        """
        Preface any logging with the current system time.
        """
        cur_time = strftime('%H:%M:%S')
        log.write('System Time: %s : %s' % (cur_time, str))

    def get_selected_neighbors(self):
        """
        Depending on the selected experiment,
        this can propogate differently.

        By default, this is all nodes.
        """
        return self.clientsHolder.allClients()

    def in_neighbors(self, port):
        """
        Returns whether this port is in this node's neighbors.
        """
        nodes = [n for n in self.get_selected_neighbors() if n[2] == port]
        if len(nodes) == 0:
            return False
        else:
            return True

    def send_neighbors(self, *args):
        msg_to_send = wrap_message(*args)
        for client, host, port in self.get_selected_neighbors():
            client.send(msg_to_send)

    def add_neighbor(self, p):
        if not self.clientsHolder.hasClient(p):
            client = Client(COORDINATOR_HOST, p)
            self.clientsHolder.addClient(client, COORDINATOR_HOST, p)

    def remove_neighbor(self, p):
        self.clientsHolder.removeClient(p)

    def listen(self):
        """
        This method is called on a seperate thread.
        It listens for any new activity on its server.

        When the server receives something new,
        we extract the action and the arguments
        and do work accordingly.
        """
        while True:
            if not self.server.queue.empty():
                outside_pid, outside_message = self.server.queue.get()
                action, uid, args = unwrap_message(outside_message)

                # Check for uid.
                if uid in self.seen:
                    continue

                self.seen[uid] = True

                if action == 'N1': # node announcement from server
                    array = eval(args[0])
                    for p in array:
                        self.add_neighbor(int(p))

                elif action == 'N2': # add neighbors (get a single node)
                    # add to neighbours
                    p = args[0]

                    # broadcast to peers that there is a new guy out there
                    self.send_neighbors('N4', p)

                    # add the neighbor
                    self.add_neighbor(int(p))

                elif action == "N3":
                    # remove neighbours
                    p = args[0]
                    self.remove_neighbor(p)

                elif action == "N4":
                    # there is a new node in the topology
                    pass


                elif action == "M": # got message
                    sender, recipient, msg = args
                    sender = int(sender)
                    recipient = int(recipient)
                    # Check if addressed to me

                    if recipient == self.port:
                        ##### DO LOGGING STUFF #####
                        print "I, {0} got a message from {1}: {2}".format(self.host, sender, msg)

                    # Check if addressed to one of my neighbors
                    elif self.in_neighbors(recipient):
                        client = self.clientsHolder.getClient(recipient)
                        msg_to_send = wrap_message("M", uid, sender, recipient, msg)
                        client.send(msg_to_send)

                    # Else, send to all my neighbors, to propogate
                    else:
                        self.send_neighbors("M", sender, recipient, msg)

    def periodically_send_messages(self):
        pass

    def start(self):
        # Setup logging
        pid = os.getpid()
        log_path = "log/log_%s" % (pid)
        log = open(log_path, "w")

        # Server for receiving messages
        self.server = Server(self.host, self.port)

        t = threading.Thread(target = self.server.serve_forever, args = ())
        t.start()

        neighbors = []

        listenThread = threading.Thread(target = self.listen, args = ())
        listenThread.start()

        client = Client(COORDINATOR_HOST, COORDINATOR_PORT)
        client.connect()

        # connect to coordinator and announce existence
        msg_to_send = wrap_message('C1', gen_uid(), self.host, self.port)
        client.send(msg_to_send)

        # Send lots of messages at random times
        self.periodically_send_messages()

        # Close logging
        log.close()

if __name__ == "__main__":
    #print sys.argv
    if len(sys.argv) != 2:
        usage()

    # Connection stats
    reliability = 0.8
    speed = 3

    HOST, PORT = make_host_port(sys.argv[1]) # server (receive)

    node = Node(HOST, PORT, reliability, speed)
    node.start()

