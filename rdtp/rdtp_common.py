import select
import socket

class ClientDead(Exception):
    def __str__(self):
        return "Client has died."

class ServerDead(Exception):
    def __str__(self):
        return "Server has died."

##################################
### Real Data Transfer Protocol
##################################
#
# Magic number (1 byte) / Version (1 byte) /  Action (1 byte) /
# Length (1 byte) / Message (Length bytes)

### Usage ###
# Top-level functions: recv, send
# - Ideally, you should only have to interface with these.

# Mid-level functions: recv_message, send_message
# - These include a variety of assertions. recv and send are wrappers for these.

# Low-level: recv_nbytes
# - keeps reading until we finish recieving what we are expecting.

RDTP_HEADER_LENGTH = 4
RDTP_MAGIC = unichr(0x42)
RDTP_VERSION = unichr(1)
ARG_LEN_MAX = 256

### High-level

def recv(sock):
    """
    recv receives a message on a socket, parses the output, and returns the different parts
    the final part of the message is assumed to be colon-delimited

    :param sock: A socket that has a message ready to be read

    :return On success, the action, response status, and a list of string arguments for the action
    """
    status, message = recv_message(sock)

    args = message.split(':')
    return status, args

def send(sock, status, *args):
    """
    send acts as a wrapper for send_message. It just makes sure that the parts of the message
    are joined by colons for later parsing. see send_message for details
    """
    send_message(sock, status, ':'.join(args))

### Mid-level

def recv_message(sock):
    """
    recv_message: receives a message formatted according to RDTP from a ready socket
    Assumes the message is in the format of RDTP.
    Assumes no dropped bytes.

    Parameters
    :param sock: a socket object. Belongs to either a client listening for a server response on its
        listener thread, or a server that has blocked on a set of sockets waiting for them
        to be ready to read

    :return On success, returns the sent action, the status code, and the message delimited by colons
    """
    # get the first 3 bytes which are spposed to be part of the preamble
    header = recv_nbytes(sock, RDTP_HEADER_LENGTH)
    assert(len(header) == RDTP_HEADER_LENGTH)

    #print header, "this is the header"

    magic, version, status, msg_len = header[0], header[1], header[2], header[3]

    # Check for malformed messages
    if magic != RDTP_MAGIC or version != RDTP_VERSION:
        #print header
        return RDTP_MALFORMED, ""
    msg_len = ord(msg_len)
    #print msg_len, "this is messages len"
    # if msg_len:
    #     msg_len = 0
    # else:
    #     msg_len = int(msg_len)
    #msg_len = 3

    # Wrong message length
    if msg_len < 0 or msg_len > ARG_LEN_MAX:
        return RDTP_MALFORMED, ""

    #print msg_len, "message length"
    # read in the expected message
    #action = recv_nbytes(sock, action_len)
    message = recv_nbytes(sock, msg_len)
    status_code = ord(status)

    return status_code, message

def send_message(sock, status, message):
    """
    send_message: sends a message according to the RDTP protocol along the provided socket object
    Assumes that message is colon-delimited.

    :param sock: the socket object along which to send the message
    :param action: specifies the specific action the sender wants the receiver to take. less than ARG_LEN_MAX.
    Actions for the server to send specify whether the message is a message from another user or a server
    response to a previously requested action. Actions for the client to send are different commands available
    to the client.
    :param status: Different possible error code. The client always sends zero as a status, while the server is
    free to send any code that the client would understand.

    """
    #print "inside send message funcction"
    msg_len = len(message)
    #print message, "this is the message ___"
    if msg_len > ARG_LEN_MAX:
      print 'Message too long'
      return False

    # action_len = len(action)
    # if action_len > ARG_LEN_MAX:
    #   print 'Action too long'
    #   return False

    #print "sending mmessages"
    # Constructs RDTP message
    to_send = RDTP_MAGIC + RDTP_VERSION + unichr(status) + unichr(msg_len)
    #to_send += action
    to_send += message
    #print len(to_send), "to send len"
    #print msg_len, "message length"
    assert(len(to_send) == RDTP_HEADER_LENGTH + msg_len)

    #print to_send, "this is what i am sending"

    # Sends the actual message
    try:
        sock.sendall(to_send)
    except:
        raise ServerDead

### Low-level

def recv_nbytes(sock, n):
    """
    recv_nbytes reads in a certain number of bytes from a socket. Blocks until it receives all requested bytes
    Assumes messages are not dropped (otherwise blocks forever)

    :param sock: socket to receive message from
    :param n: number of bytes to read

    """
    #print n, "this is "
    bytes_received = 0
    received = ""
    # keep on reading until we get what we expected
    while bytes_received < n:
        ready_to_read,_,_ = select.select([sock],[],[])
        data = sock.recv(1, socket.MSG_PEEK)
        #rint data, "this is the data"

        if len(data) == 0:
            raise ClientDead
        else:
            assert(ready_to_read != [])
            new_recv = sock.recv(n - bytes_received)
            bytes_received += len(new_recv)
            received += new_recv
    assert(bytes_received == len(received))
    return received

