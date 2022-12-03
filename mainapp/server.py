from socket import socket, AF_INET, SOCK_STREAM
from select import select
from time import sleep

from descriptors import Port
from common.variables import MAX_PACKAGE_SIZE, ACTION, PRESENCE, USER, ACCOUNT_NAME, RESPONSE_200, \
    ERROR, SENDER, EXIT, MESSAGE, RESPONSE_400, DESTINATION, TIME, MESSAGE_TEXT, RESPONSE_201
from server_database import ServerStorage
from metaclasses import ServerVerifier
from common.utils import get_host_port, send_message, get_message
from common import variables


class Server(metaclass=ServerVerifier):
    port = Port()

    def __init__(self):
        self.server_storage = ServerStorage()
        self.host, self.port = get_host_port()
        self.client_sockets = []
        self.messages = []
        self.names = dict()

    def run(self):
        with socket(AF_INET, SOCK_STREAM) as server_sock:
            server_sock.bind((self.host, self.port))
            server_sock.listen(variables.SERVER_MAX_LISTEN)
            server_sock.settimeout(variables.SERVER_SETTIMEOUT)

            while True:
                try:
                    client, addr = server_sock.accept()
                except TimeoutError:
                    pass
                else:
                    self.client_sockets.append(client)
                finally:
                    try:
                        writers_list, getters_list = [], []
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
                                self.process_client_message(writer)
                            except Exception:
                                self.client_sockets.remove(writer)
                                writer.close()
                    for message in self.messages:
                        try:
                            self.process_message(message, getters_list)
                        except ConnectionError:
                            try:
                                del self.names[message[DESTINATION]]
                            except KeyError:
                                pass
                            self.client_sockets.remove(self.names[message[DESTINATION]])
                    self.messages.clear()

    def process_message(self, message, getters_list):
        """
        Парсинг сообщения типа клиент-клиент
        """
        if message[DESTINATION] in self.names and self.names.get(message[DESTINATION]) in getters_list:
            send_message(self.names[message[DESTINATION]], message)
        elif message[DESTINATION] in self.names and self.names.get(DESTINATION) not in getters_list:
            raise ConnectionError
        else:
            response = RESPONSE_400
            response[MESSAGE_TEXT] = 'Пользователь не найден'
            send_message(self.names[message[SENDER]], response)

    def process_client_message(self, client_sock):
        """
        Парсит сообщение от клиентского
        сокета и возвращает ответ.
        В случае, если сообщение не вида клиент-клиент или оно
        некорректно, то отправляет ответ пользователю
        """
        message = get_message(client_sock)
        print(message)
        # Если сообщение представление, то отвечаем пользователю
        if message[ACTION] == PRESENCE:
            if message[SENDER] not in self.names.keys():
                self.names[message[SENDER]] = client_sock
                ip, port = client_sock.getpeername()
                # self.server_storage.login(message[SENDER], ip, port)
                response = RESPONSE_200
                response[MESSAGE_TEXT] = 'Добро пожаловать!'
                send_message(client_sock, response)
            else:
                send_message(client_sock, RESPONSE_201)
        # Сообщение о выходе
        elif message[ACTION] == EXIT:
            response = RESPONSE_200
            response[MESSAGE_TEXT] = 'До свидания!'
            send_message(client_sock, response)
            self.client_sockets.remove(self.names[message[SENDER]])
            client_sock.close()
            del self.names[message[SENDER]]
        # Сообщение клиент-клиент
        elif (message[ACTION] == MESSAGE and
              message[SENDER] and
              message[DESTINATION] and
              message[TIME]):
            self.messages.append(message)
        else:
            response = RESPONSE_400
            response[MESSAGE_TEXT] = 'Некорректный запрос'
            send_message(client_sock, response)


if __name__ == '__main__':
    server = Server()
    server.run()
