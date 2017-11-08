import threading
from time import sleep

import socket
import sys
import re

# Current node's IP
NODE_IP = '127.0.0.1'  # '200.0.2.4'
NODE_PORT = 12345

# Dispatcher's IP
DISPATCHER_IP = '127.0.0.1'
DISPATCHER_PORT = 10000

# Router's IP
ROUTER_IP = '127.0.0.1'
ROUTER_PORT = 10001

# Array of other computers on net
net_bros = []


def main():
    node = Node()
    node.start()
    try:
        join_threads(node.threads)
    except KeyboardInterrupt:
        print ("\nKeyboardInterrupt catched.")
        print ("Terminate main thread.")
        print ("If only daemonic threads are left, terminate whole program.")


# Class for single nodes
class Node(object):
    def __init__(self):
        self.running = True
        self.threads = []

    def start(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print('Socket created')

        try:
            soc.bind((NODE_IP, NODE_PORT))
            print('Socket bind complete')

        except socket.error as msg:
            import sys
            print('Bind failed. Error : ' + str(sys.exc_info()))
            sys.exit()

        # Start listening on socket
        soc.listen(10)
        print('Socket now listening')

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = (ROUTER_IP, ROUTER_PORT)
        print('connecting to {} port {}'.format(*server_address))

        try:
            sock.connect(server_address)

        except Exception as e:
            print("Something's wrong with %s:%d."
                  "\nException is %s" % (ROUTER_IP, ROUTER_PORT, e))

        while self.running:

            package_msg = input("Enter the message: ")
            print('sending {!r}'.format(package_msg))
            sock.send(package_msg.encode())
                #
                # # Look for the response
                # amount_received = 0
                # amount_expected = len(package_msg)
                #
                # while amount_received < amount_expected:
                #     data = sock.recv(200)
                #     amount_received += len(data)
                #     print('received {!r}'.format(data))
                #     break
        sock.close()


def join_threads(threads):
    """
    Join threads in interruptable fashion.
    From http://stackoverflow.com/a/9790882/145400
    """
    for t in threads:
        while t.isAlive():
            t.join(5)


if __name__ == "__main__":
    main()