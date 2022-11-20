import sys
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread
from time import sleep

from descriptors import Port
from metaclasses import ClientVerifier
from utils import get_host_port


class Client(metaclass=ClientVerifier):
    port = Port()

    def __init__(self):
        self.host, self.port = get_host_port()

    def run(self):
        with socket(AF_INET, SOCK_STREAM) as client_sock:
            try:
                client_sock.connect((self.host, self.port))
            except ConnectionRefusedError as e:
                sys.exit(1)
            except OSError as e:
                print('Подключение уже установлено')

            user_interface_thread = Thread(
                target=self.user_interface, args=(client_sock,), daemon=True)
            reciever_interface_thread = Thread(
                target=self.reciever_interface, args=(client_sock,), daemon=True)
            print('Для выхода введите exit')
            user_interface_thread.start()
            reciever_interface_thread.start()
            while True:
                sleep(1)
                if user_interface_thread.is_alive() and \
                        reciever_interface_thread.is_alive():
                    continue
                break

    def reciever_interface(self, sock):
        while True:
            data = sock.recv(4096)
            print(data.decode('utf-8'))

    def user_interface(self, sock):
        while True:
            message = input()
            if message == 'exit':
                break
            sock.send(message.encode('utf-8'))


if __name__ == '__main__':
    client = Client()
    client.run()
