class ClientsHolder(object):
    def __init__(self):
        """
        Setup the clients holder.
        """
        self.clients = {}

    def addClient(self, client, host, port):
        """
        Add a client to the holder
        """
        port = int(port)
        self.clients[port] = (client, host, port)

    def hasClient(self, port):
        """
        Check if we have a client with this port already.
        """
        port = int(port)
        return (port in self.clients)

    def getClient(self, port):
        """
        Get a client from the holder.
        Make sure you check if it exists first!
        """
        try:
            port = int(port)
            client, host, port = self.clients[port]
            return client
        except KeyError:
            print "========= No client exists with port {0}. Please use hasClient first.".format(port)

    def allClients(self):
        """
        Return a list of all client objects.
        """
        return self.clients.values()

    def removeClient(self, port):
        port = int(port)
        del self.clients[port]
