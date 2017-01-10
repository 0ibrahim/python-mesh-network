from rdtp.rdtp_client import Client
from rdtp.rdtp_server import Server
import thread
import sys, os
from clientsHolder import ClientsHolder
from time import strftime
import threading
from messageWrapper import wrap_message, unwrap_message, gen_uid
from clientsHolder import ClientsHolder

class Coordinator:
    """
    Implements logic for the coordinator on the mesh network.
    Indeed, a `coordinator` does not really exist in a mesh network.

    Here, we implement a coordinator for the sole purpose of positioning the nodes
    in a manifold. The coordinator is used to running experiments (logging)
    and for telling nodes who is nearby them, in the geography.
    """

    def __init__(self):
        self.server = None
        self.num_nodes = 0
        self.clientsHolder = ClientsHolder()

    def neighbors(self, port):
        port = int(port)
        res = []
        for p in [port-1, port+1]:
            if self.clientsHolder.hasClient(p):
                res.append(p)
        return res

    def usage(self):
        print "Usage: python coordinator.py HOST:PORT"
        exit()

    def add_node(self, client, host, port):
        # Find this node's neighbors - we do this first
        # so that the new node does not show up as his own neighbor :)
        neighbors = self.neighbors(port)

        # Add this node to our toplogy
        self.clientsHolder.addClient(client, host, port)
        self.num_nodes += 1

        # Notify neighbors of this new node
        for neighbor_p in neighbors:
            self.notify_add(neighbor_p, port)

        return neighbors

    def remove_node(self, host, port):
        # Remove this node from our topology
        self.clientsHolder.removeClient(port)
        self.num_nodes -= 1

        # Find this node's neighbors - we do this second
        # because we do not want the node himself to come up in this.
        neighbors = self.neighbors(host, port)

        # notify neighbors that the node has been removed
        for neighbor_p in neighbors:
            self.notify_remove(neighbor_p, port)

    def notify_add(self, port_existing, port_new):
        """
        Notifies some node that a new one has joined.
        """
        client = self.clientsHolder.getClient(port_existing)
        msg_to_send = wrap_message("N2", gen_uid(), client)
        client.send(msg_to_send)

    def notify_remove(self, port_existing, port_new):
        """
        Notifies some node that a new one has been removed.
        """
        client = self.clientsHolder.getClient(port_existing)
        msg_to_send = wrap_message("N3", gen_uid(), client)
        client.send(msg_to_send)

    def make_host_port(self, arg):
        args = arg.split(':')
        return args[0], int(args[1])

    def start(self):
        #print sys.argv
        if len(sys.argv) != 2:
            self.usage()

        # Setup logging
        pid = os.getpid()
        log_path = "log/log_%s" % (pid)
        log = open(log_path, "w")

        # Server for receiving messages
        HOST, PORT = self.make_host_port(sys.argv[1]) # server (receive)
        self.server = Server(HOST, PORT)
        #print "helloq"
        #thread.start_new_thread(server.serve_forever, ())
        t = threading.Thread(target = self.server.serve_forever, args = ())
        t.start()
        #server.serve_forever

        #print "it goes forward"
        # Client for talking to coordinator


        #print "send"
        # Continually listen for new neighbors (there will be many announcements in the beginning)
        neighbors = []
        def listen():
            while True:
                #print "this is happending in the server"
                if not self.server.queue.empty():
                    print "coordinator got a message"
                    print "something in queue"
                    outside_pid, outside_message = self.server.queue.get()
                    action, uid, args = unwrap_message(outside_message)

                    if action == 'C1': # node announcement from server
                        host = args[0]
                        port = args[1]

                        print "this is the host and port", host, port

                        #Spin up a client
                        c = Client(host, port)
                        c.connect()
                        self.add_node(c, host, port)
                        nei = self.neighbors(port)
                        print nei, "neighbors"

                        #Send back client list (send it to c)
                        c.send(wrap_message("N1", gen_uid(), nei))

                    if action == 'C2': # delete a node
                        host = args[0]
                        port = args[1]

                        # Delete that client
                        self.remove_node(host, port)

        listenThread = threading.Thread(target = listen, args = ())
        listenThread.start()
        print "coordinator is up"

c = Coordinator()
c.start()

