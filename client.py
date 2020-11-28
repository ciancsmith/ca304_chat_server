#!/usr/bin/env python3

import threading
import socket
import argparse
import os
import sys
import tkinter as tk
import pickle

HOST = "192.168.1.94"
PORT = 4201

class Send(threading.Thread):
    """
    Sending thread listens for user input from the command line.
    Attributes:
        sock (socket.socket): The connected socket object.
        name (str): The username provided by the user.
    """
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name

    def run(self):
        """
        Listens for user input from the command line only and sends it to the server.
        Typing 'QUIT' will close the connection and exit the application.
        """
        while True:
            print('{}: '.format(self.name), end='')
            sys.stdout.flush()
            message = sys.stdin.readline()[:-1]

            # Type 'QUIT' to leave the chatroom
            if message == 'QUIT':
                self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('utf-8'))
                break
            
            # Send message to server for broadcasting
            else:
                self.sock.sendall('{}: {}'.format(self.name, message).encode('utf-8'))
        
        print('\nQuitting...')
        self.sock.close()
        os._exit(0)


class Receive(threading.Thread):
    """
    Receiving thread listens for incoming messages from the server.
    Attributes:
        sock (socket.socket): The connected socket object.
        name (str): The username provided by the user.
        messages (tk.Listbox): The tk.Listbox object containing all messages displayed on the GUI.
    """
    def __init__(self, sock, name):
        super().__init__()
        self.sock = sock
        self.name = name
        self.messages = None

    def run(self):
        """
        Receives data from the server and displays it in the GUI.
        Always listens for incoming data until either end has closed the socket.
        """
        while True:
            message = self.sock.recv(1024).decode('utf-8')

            if message:

                if self.messages:
                    self.messages.insert(tk.END, message)
                    print('hi')
                    print('\r{}\n{}: '.format(message, self.name), end = '')
                
                else:
                    # Thread has started, but client GUI is not yet ready
                    print('\r{}\n{}: '.format(message, self.name), end = '')
            
            else:
                # Server has closed the socket, exit the program
                print('\nOh no, we have lost connection to the server!')
                print('\nQuitting...')
                self.sock.close()
                os._exit(0)

class Client:
    """
    Supports management of client-server connections and integration with the GUI.
    Attributes:
        host (str): The IP address of the server's listening socket.
        port (int): The port number of the server's listening socket.
        sock (socket.socket): The connected socket object.
        name (str): The username of the client.
        messages (tk.Listbox): The tk.Listbox object containing all messages displayed on the GUI.
    """
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None
        self.channel = None
        self.messages = None
        
            
    def start(self):
        """
        Establishes the client-server connection. Gathers user input for the username,
        creates and starts the Send and Receive threads, and notifies other connected clients.
        Returns:
            A Receive object representing the receiving thread.
        """
        print('Trying to connect to {}:{}...'.format(self.host, self.port))
        self.sock.connect((self.host, self.port))
        print('Successfully connected to {}:{}'.format(self.host, self.port))
        
        print()
        self.name = input('Your name: ')
        self.channel = input('Enter the channel you would like to join "A-Z"')
        info = self.name, self.channel
        data = {'name': info[0], 'channel': info[1]}
        print(data)
        data = pickle.dumps(data) 
        self.sock.sendall(data)
        


        print()
        print('Welcome, {}! Getting ready to send and receive messages...'.format(self.name))

        # Create send and receive threads
        send = Send(self.sock, self.name)
        receive = Receive(self.sock, self.name)

        # Start send and receive threads
        send.start()
        receive.start()

        self.sock.sendall('Server: {} has joined the chat. Say hi!'.format(self.name).encode('utf-8'))
        print("\rAll set! Leave the chatroom anytime by typing 'QUIT'\n")
        print('{}: '.format(self.name), end = '')

        return receive

    def send(self, text_input):
        """
        Sends text_input data from the GUI. This method should be bound to text_input and 
        any other widgets that activate a similar function e.g. buttons.
        Typing 'QUIT' will close the connection and exit the application.
        Args:
            text_input(tk.Entry): A tk.Entry object meant for user text input.
        """
        message = text_input.get()
        text_input.delete(0, tk.END)
        self.messages.insert(tk.END, '{}: {}'.format(self.name, message))
        
        

        # Type 'QUIT' to leave the chatroom
        if message == 'QUIT':
            self.sock.sendall('Server: {} has left the chat.'.format(self.name).encode('utf-8'))
            
            print('\nQuitting...')
            self.sock.close()
            os._exit(0)
        
        # Send message to server for broadcasting
        else:
            self.sock.sendall('{}: {}'.format(self.name, message).encode('utf-8'))


def main(host, port):
    """
    Initializes and runs the GUI application.
    Args:
        host (str): The IP address of the server's listening socket.
        port (int): The port number of the server's listening socket.
    """
    client = Client(host, port)
    receive = client.start()

    window = tk.Tk()
    window.title('Chatroom {}'.format(client.channel))

    frm_messages = tk.Frame(master=window, bg="#434046")
    scrollbar = tk.Scrollbar(master=frm_messages,  bg="#434046", activebackground="#767676")
    messages = tk.Listbox(
        master=frm_messages, 
        yscrollcommand=scrollbar.set,
        bg = "#434046",
        fg = "#fff9f9"
    )
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, expand=False)
    messages.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    client.messages = messages
    receive.messages = messages

    frm_messages.grid(row=0, column=0, columnspan=2, sticky="nsew")

    frm_entry = tk.Frame(master=window, bg="#434046")
    text_input = tk.Entry(master=frm_entry, bg="#434046", fg = "#fff9f9")
    text_input.pack(fill=tk.BOTH, expand=True)
    text_input.bind("<Return>", lambda x: client.send(text_input))
    text_input.insert(0, "Your message here.")

    btn_send = tk.Button(
        master=window,
        text='Send',
        bg="#434046",
        fg = "#fff9f9",
        activebackground="#767676",
        command=lambda: client.send(text_input)
    )

    frm_entry.grid(row=1, column=0, padx=10, sticky="ew")
    btn_send.grid(row=1, column=1, pady=10, sticky="ew")

    window.rowconfigure(0, minsize=500, weight=1)
    window.rowconfigure(1, minsize=50, weight=0)
    window.columnconfigure(0, minsize=500, weight=1)
    window.columnconfigure(1, minsize=200, weight=0)
    window.configure(bg = "#434046")

    window.mainloop()


if __name__ == '__main__':
    
    main(HOST, PORT)