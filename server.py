#!/usr/bin/env python3

import threading
import socket
import argparse
import os
import pickle

#This was my raspberry pi internal address Don't hurt me :(
#change the HOST variable to whatever suits your system I should however have it running from my IP address
#if port forwarding will allow it
HOST = "192.168.1.94"
PORT = 4201

class Server(threading.Thread):
    """
    Supports management of server connections.
    Attributes:
        connections (list): A list of ServerSocket objects representing the active connections.
        host (str): The IP address of the listening socket.
        port (int): The port number of the listening socket.
    """
    def __init__(self, host, port):
        super().__init__()
        self.connections = []
        self.clients = {}
        self.channels = {}
        self.host = host
        self.port = port
    
    def run(self):
        """
        Creates the listening socket. The listening socket will use the SO_REUSEADDR option to
        allow binding to a previously-used socket address. This is a small-scale application which
        only supports one waiting connection at a time. 
        For each new connection, a ServerSocket thread is started to facilitate communications with
        that particular client. All ServerSocket objects are stored in the connections attribute.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))

        sock.listen(1)
        print('Listening at', sock.getsockname())

        while True:

            # Accept new connection
            sc, sockname = sock.accept()
            print('Accepted a new connection from {} to {}'.format(sc.getpeername(), sc.getsockname()))

            # Create new thread
            server_socket = ServerSocket(sc, sockname, self)
            
            # Start new thread
            server_socket.start()

            # Add thread to active connections
            self.connections.append(server_socket)
            print('Ready to receive messages from', sc.getpeername())

    def broadcast(self, message, source):
        """
        Sends a message to all connected clients, except the source of the message.
        Args:
            message (str): The message to broadcast.
            source (tuple): The socket address of the source client.
        """
        #updated this so it does it for channels
        channel = self.clients[source.sockname]['channel']
        print(channel)
        for client in self.channels[channel]:
            if client.sockname != source.sockname:
                client.send(message)
            
        
            
            # # Send to all connected clients except the source client
            # if connection.sockname != source.sockname:
                
            #     if self.channels[connection.sockname]['channel'] == self.channels[source.sockname]['channel']:
            #         print("im here")
            #         connection.send(message)
    
    def remove_connection(self, connection):
        """
        Removes a ServerSocket thread from the connections attribute.
        Args:
            connection (ServerSocket): The ServerSocket thread to remove.
        """
        self.connections.remove(connection)


class ServerSocket(threading.Thread):
    """
    Supports communications with a connected client.
    Attributes:
        sc (socket.socket): The connected socket.
        sockname (tuple): The client socket address.
        server (Server): The parent thread.
    """
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server
    
    def run(self):
        """
        Receives data from the connected client and broadcasts the message to all other clients.
        If the client has left the connection, closes the connected socket and removes itself
        from the list of ServerSocket threads in the parent Server thread.
        """
        while True:
            message = self.sc.recv(1024)
            try:
                message = message.decode('utf-8')

                    
                                
                if message:
                    print('{} says {!r}'.format(self.sockname, message))
                    self.server.broadcast(message, self)
                else:
                # Client has closed the socket, exit the thread
                    print('{} has closed the connection'.format(self.sockname))
                    self.sc.close()
                    server.remove_connection(self)
                    return
            
            except UnicodeDecodeError as e:
                #trying to decode object as utf-8 unable we will use this as a flag to show the user is sending username and channel
                #we could have an if statement to check the contents of the object if we wanted to implement files etc
                message = pickle.loads(message)
                
                if 'name' in message.keys():
                    
                    self.server.clients[self.sockname] = message
                    
                    if self.server.clients[self.sockname]['channel'] not in self.server.channels.keys():
                        
                        print('Creating Channel {} for use'.format(self.server.clients[self.sockname]['channel']))
                        self.server.channels[self.server.clients[self.sockname]['channel']] = []
                        
                    
                    self.server.channels[self.server.clients[self.sockname]['channel']].append(self)
                    print("Connecting {} to channel {}".format(self.sockname, self.server.clients[self.sockname]['channel']))
                    
                    
                    

    def send(self, message):
        """
        Sends a message to the connected server.
        Args:
            message (str): The message to be sent.
        """
        self.sc.sendall(message.encode('utf-8'))


def exit(server):
    """
    Allows the server administrator to shut down the server.
    Typing 'q' in the command line will close all active connections and exit the application.
    """
    while True:
        ipt = input('')
        if ipt == 'q':
            print('Closing all connections...')
            for connection in server.connections:
                connection.sc.close()
            print('Shutting down the server...')
            os._exit(0)


if __name__ == '__main__':
    # Create and start server thread
    server = Server(HOST, PORT)
    server.start()

    exit = threading.Thread(target = exit, args = (server,))
    exit.start()