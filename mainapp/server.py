from socket import socket, AF_INET, SOCK_STREAM
from select import select

from descriptors import Port
from metaclasses import ServerVerifier
from utils import get_host_port
import settings


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self):
        self.host, self.port = get_host_port()
        self.client_sockets = []
        self.messages = []

    def run(self):
        with socket(AF_INET, SOCK_STREAM) as server_sock:
            server_sock.bind((self.host, self.port))
            server_sock.listen(settings.SERVER_MAX_LISTEN)
            server_sock.settimeout(settings.SERVER_SETTIMEOUT)

            while True:
                try:
                    client, addr = server_sock.accept()
                except TimeoutError:
                    pass
                else:
                    self.client_sockets.append(client)
                finally:
                    writers_list, getters_list = [], []
                    try:
                        writers_list, getters_list, _ = select(
                            self.client_sockets,
                            self.client_sockets,
                            [],
                            0,
                        )
                    except OSError:
                        pass
                    if writers_list:
                        for writer in writers_list:
                            try:
                                data = writer.recv(4096)
                                message = data.decode('utf-8')
                                self.messages.append(message)
                            except Exception:
                                self.client_sockets.remove(client)
                    if getters_list and self.messages:
                        message = self.messages[0]
                        del self.messages[0]
                        for getter in getters_list:
                            try:
                                getter.send(message.encode('utf-8'))
                            except Exception:
                                self.client_sockets.remove(getter)


if __name__ == '__main__':
    server = Server()
    server.run()
