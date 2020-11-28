#!/bin/env_python3

class ServerSocket(threading.Thread):
    """
    docstring
    """
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server
        
        
    def run(self):
        while True:
            message = self.sc.recv(1024).decode('ascii')
            if message:
                print('{} says {!r}'.format(self.sockname, message))
                self.server.broadcast(message, self.sockname)
            else:
                #Client has closed the socket, exit the thread
                print('{} has closed the connection'.format(self.sockname))
                self.sc.close()
                server.remove_connection(self)
                return
            
    def send(self, message):
        self.sc.sendall(message.encode('ascii'))
                