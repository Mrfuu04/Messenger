import configparser
import os
import sys
from socket import socket, AF_INET, SOCK_STREAM
from select import select
from threading import Thread
from time import sleep

from PyQt5.QtWidgets import QApplication

from descriptors import Port
from common.variables import ACTION, PRESENCE, RESPONSE_200, \
    SENDER, EXIT, MESSAGE, RESPONSE_400, DESTINATION, TIME, MESSAGE_TEXT, RESPONSE_201, CONTACTS, ADD_CONTACT, \
    DEL_CONTACT, REGISTER, NICKNAME_IN_USE, RESPONSE_401
from gui.server_gui import ServerGui
from server_db.server_database import ServerStorage
from common.metaclasses import ServerVerifier
from common.utils import get_host_port, send_message, get_message
from common import variables


class Server(
    metaclass=ServerVerifier,
):
    port = Port()

    def __init__(self, config_file_path):
        self.config_file_path = config_file_path
        self.config = configparser.ConfigParser()
        self.config.read(config_file_path)

        self.server_storage = ServerStorage(self.config)
        self.host, self.port = get_host_port(self.config)
        self.client_sockets = []
        self.messages = []
        self.names = dict()

    def run(self):
        frontside = Thread(
            target=self._frontside,
            daemon=True,
        )
        backside = Thread(
            target=self._backside,
            daemon=True,
        )
        gui = Thread(
            target=self._run_gui,
            args=(self.config_file_path,),
            daemon=True,
        )
        # frontside.start()
        backside.start()
        gui.start()

        while True:
            sleep(1)
            if backside.is_alive() and gui.is_alive():
                continue
            sys.exit()

    def _run_gui(self, config_file_path):
        """
        Поток графического клиента для сервера.
        """
        server_app = QApplication(sys.argv)

        server_gui = ServerGui(config_file_path, self.server_storage)
        server_gui.set_timer(3000)
        server_gui.show()

        sys.exit(server_app.exec())

    def _frontside(self):
        """
        Поток консольного управления.
        """
        print('*** Для вывода справки введите help ***')
        while True:
            command = input('Введите команду: ')
            if command == 'help':
                print(self.__print_help_message())
            elif command == 'userlist':
                print(self.get_userlist())
            elif command == 'online':
                print(self.get_online_users())
            elif command == 'history':
                print(self.get_loginhistory())
            elif command == 'exit':
                sys.exit()

    def _backside(self):
        """
        Поток обработки сообщений.
        """
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
                            except Exception as e:
                                # Отрефакторить
                                try:
                                    connection_lost_username = list(
                                        self.names.keys())[list(self.names.values()).index(writer)]
                                    self._end_connection_with_client(connection_lost_username)
                                except ValueError:
                                    self.client_sockets.remove(writer)
                                    writer.close()
                    for message in self.messages:
                        try:
                            self.process_message(message, getters_list)
                        except ConnectionError:
                            self._end_connection_with_client(message[DESTINATION])

                    self.messages.clear()

    def process_message(self, message, getters_list):
        """
        Парсинг сообщения типа клиент-клиент
        """
        if message[DESTINATION] in self.names and self.names.get(message[DESTINATION]) in getters_list:
            send_message(self.names[message[DESTINATION]], message)
            self.server_storage.update_user_msg_counts(message[SENDER],
                                                       message[DESTINATION])
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

        # Если сообщение представление, то отвечаем пользователю
        if message[ACTION] == PRESENCE:
            if message[SENDER] not in self.names.keys():
                authenticate = self.server_storage.authenticate(
                    message[SENDER],
                    message[MESSAGE_TEXT],
                )
                if authenticate:
                    self.names[message[SENDER]] = client_sock
                    ip, port = client_sock.getpeername()
                    self.server_storage.login(message[SENDER], ip, port)
                    response = RESPONSE_200
                    response[MESSAGE_TEXT] = 'Добро пожаловать!'
                    send_message(client_sock, response)
                else:
                    response = RESPONSE_401
                    response[MESSAGE_TEXT] = 'Логин или пароль неверные'
                    send_message(client_sock, response)
                    self.client_sockets.remove(client_sock)
                    client_sock.close()
            else:
                send_message(client_sock, RESPONSE_201)

        # Сообщение о выходе
        elif message[ACTION] == EXIT:
            response = RESPONSE_200
            response[MESSAGE_TEXT] = 'До свидания!'
            send_message(client_sock, response)
            self._end_connection_with_client(message[SENDER])

        # Сообщение клиент-клиент
        elif (message[ACTION] == MESSAGE and
              message[SENDER] and
              message[DESTINATION] and
              message[TIME]):
            self.messages.append(message)

        # Запрос на список контактов
        elif message[ACTION] == CONTACTS:
            contacts = self.server_storage.get_user_contacts(
                message[SENDER]
            )
            response = RESPONSE_200
            response[MESSAGE_TEXT] = contacts
            send_message(client_sock, response)

        # Добавление контакта
        elif message[ACTION] == ADD_CONTACT:
            response = RESPONSE_200
            if message[SENDER] == message[MESSAGE_TEXT]:
                response[MESSAGE_TEXT] = 'Вы не можете добавить сами себя'
            else:
                created = self.server_storage.add_contact(
                    message[SENDER],
                    message[MESSAGE_TEXT],
                )
                if created:
                    response[MESSAGE_TEXT] = f'Пользователь {message[MESSAGE_TEXT]} добавлен'
                else:
                    response[MESSAGE_TEXT] = f'Ошибка при добавлении пользователя'
            send_message(client_sock, response)

        # Удаление контакта
        elif message[ACTION] == DEL_CONTACT:
            deleted = self.server_storage.del_contact(
                message[SENDER],
                message[MESSAGE_TEXT],
            )
            response = RESPONSE_200
            if deleted:
                response[MESSAGE_TEXT] = f'Пользователь {message[MESSAGE_TEXT]} удален'
            else:
                response[MESSAGE_TEXT] = f'Ошибка при удалении пользователя'
            send_message(client_sock, response)
        
        # Регистрация
        elif message[ACTION] == REGISTER:
            registered = self.server_storage.register_user(
                message[SENDER],
                message[MESSAGE_TEXT],
            )
            response = RESPONSE_200
            if registered == NICKNAME_IN_USE:
                response = RESPONSE_201
            elif registered:
                response[MESSAGE_TEXT] = f'{message[SENDER]} Вы зарегистрированы!'
            else:
                response[MESSAGE_TEXT] = f'Ошибка при регистрации'
            send_message(client_sock, response)
        else:
            response = RESPONSE_400
            response[MESSAGE_TEXT] = 'Некорректный запрос'
            send_message(client_sock, response)

    def get_userlist(self):
        users = self.server_storage.get_userlist()
        out_msg = 'Список пользователей: \n'
        for user in users:
            login, _, _, date = user
            out_msg += f'{login}, последний логин: {date.strftime("%D %T")}\n'

        return out_msg

    def get_online_users(self):
        users = self.server_storage.get_online_users()
        out_msg = 'Список пользователей онлайн: \n'
        for user in users:
            login, ip, date, _ = user
            out_msg += f'{login} {ip}, время подключения {date.strftime("%D %T")}\n'

        return out_msg

    def get_loginhistory(self):
        users = self.server_storage.get_loginhistory()
        out_msg = 'Список коннектов: \n'
        for user in users:
            login, ip, port, last_conn = user
            out_msg += f'{login} {ip}:{port} {last_conn}\n'

        return out_msg

    def _end_connection_with_client(self, username):
        """
        Метод отключения клиента от сервера
        """
        self.server_storage.logout(username)
        self.client_sockets.remove(self.names[username])
        self.names.get(username).close()
        try:
            del self.names[username]
        except KeyError:
            pass

    def __print_help_message(self):
        help_message = """Доступные команды: 
        userlist - список всех пользователей
        online - список подключённых пользователей
        history - история подключений
        exit - завершение работы сервера
        help - помощь"""

        return help_message


if __name__ == '__main__':
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.relpath(__file__))
    config_file_path = os.path.join(dir_path, 'conf.ini')
    server = Server(config_file_path=config_file_path)
    server.server_storage.get_user_contacts('test')
    server.run()
