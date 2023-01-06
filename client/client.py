import sys
from hashlib import sha256
from socket import (
    AF_INET, 
    SOCK_STREAM, 
    socket,
)
from threading import (
    Lock,
    Thread,
)
from time import (
    sleep,
    time,
)

from common.metaclasses import ClientVerifier
from common.transport import Transport
from common.utils import (
    MessageCreator, 
    get_host_port, 
    get_message,
    send_message,
)
from common.variables import (
    MESSAGE_TEXT,
    RESPONSE,
    RESPONSE_200,
    RESPONSE_201, 
    SENDER,
)
from descriptors import Port
from gui.auth import ClientAuth
from gui.main_form import ClientGui
from PyQt5.QtWidgets import (
    QApplication,
    QMessageBox,
)


class Client(metaclass=ClientVerifier):
    port = Port()

    def __init__(self):
        self.host, self.port = get_host_port()
        self.message_creator = MessageCreator()
        # лок для сокета
        self.sock_lock = Lock()

    def run_gui(self):
        """
        Метод запуска клиентского приложения с ГУИ
        """
        # Первичное окно авторизации и регистрации
        self.auth_app = QApplication(sys.argv)
        self.auth_form = ClientAuth()
        self.auth_form.confirmBtn.clicked.connect(self._auth)
        self.auth_form.show()
        self.auth_app.exec_()

        # Основное окно клиента
        self.transport = Transport(
            self.client_sock,
            self.username,
        )
        self.transport.daemon = True
        self.transport.start()

        self.client_app = QApplication(sys.argv)
        self.client_gui = ClientGui(self.transport)
        self.client_gui.make_connection(self.transport)
        self.client_gui.show()
        sys.exit(self.client_app.exec_())

        self.transport.join()

    def _auth(self):
        self.username = self.auth_form.username.text()
        password = self.auth_form.password.text().encode('utf-8')
        if not self.username or not password:
            return QMessageBox.question(
                self.auth_form,
                'Внимание',
                'Все поля обязательны',
                QMessageBox.Ok,
            )
        self.client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            self.client_sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            QMessageBox.question(
                self.auth_form,
                'Внимание',
                'Связь с сервером не установлена',
                QMessageBox.Ok,
            )
            sys.exit()
        except OSError:
            pass

        password_hash = sha256(password).hexdigest()
        presence = self.message_creator.create_presence(
            self.username,
            password_hash
        )
        send_message(self.client_sock, presence)
        presence_response = get_message(self.client_sock)
        answer_message = QMessageBox()
        if presence_response[RESPONSE] == RESPONSE_200:
            answer_message.question(
                self.auth_form,
                'Авторизация',
                'Добро пожаловать',
                QMessageBox.Ok,
            )
            self.auth_form.good_exit = True
            self.auth_form.close()
        else:
            answer_message.question(
                self.auth_form,
                'Внимание',
                presence_response[MESSAGE_TEXT],
                QMessageBox.Ok,
            )

    def run(self):
        """
        Запуск клиентского приложение в консольном формате
        """
        client_sock = socket(AF_INET, SOCK_STREAM)
        try:
            client_sock.connect((self.host, self.port))
        except ConnectionRefusedError:
            sys.exit(1)
        except OSError:
            print('Подключение уже установлено')

        self.login(client_sock)

        user_interface_thread = Thread(
            target=self.user_interface, args=(client_sock,), daemon=True)
        reciever_interface_thread = Thread(
            target=self.reciever_interface, args=(client_sock,), daemon=True)
        user_interface_thread.start()
        reciever_interface_thread.start()
        while True:
            sleep(1)
            if user_interface_thread.is_alive() and \
                    reciever_interface_thread.is_alive():
                continue
            break

    def reciever_interface(self, sock):
        """Интерфейс получения сообщения"""
        while True:
            try:
                message = get_message(sock)
                print(f'{message[SENDER]}: {message[MESSAGE_TEXT]}')
            except:
                break

    def user_interface(self, sock):
        """Интерфейс пользовательского ввода"""
        print('*** Для вывода всех доступных команд введите help ***')
        while True:
            command = input('Введите команду: ')
            if command == 'help':
                self.get_help_message()
            elif command == 'message':
                destination = input('Введите имя получателя: ')
                message = self.message_creator.create_message(self.username, destination)
                send_message(sock, message)
            elif command == 'exit':
                message = self.message_creator.create_exit_message(self.username)
                send_message(sock, message)
                sleep(1)
                break
            elif command == 'contacts':
                message = self.message_creator.create_contacts_request(self.username)
                with self.sock_lock:
                    send_message(sock, message)
            elif command == 'add_contact':
                destination = input('Введите имя пользователя: ')
                message = self.message_creator.create_add_contact_request(
                    self.username,
                    destination)
                with self.sock_lock:
                    send_message(sock, message)
            elif command == 'del_contact':
                destination = input('Введите имя пользователя: ')
                message = self.message_creator.create_del_contact_request(self.username,
                                                                          destination)
                with self.sock_lock:
                    send_message(sock, message)
            else:
                print('Неопознанная команда')

    def login(self, sock):
        while True:
            self.username = input('Введите имя пользователя: ')
            password = input('Введите пароль: ').encode('utf-8')
            password_hash = sha256(password).hexdigest()
            presence = self.message_creator.create_presence(
                self.username,
                password_hash,
            )
            send_message(sock, presence)
            presence_response = get_message(sock)
            if presence_response[RESPONSE] == RESPONSE_201:
                print(presence_response[MESSAGE_TEXT])
            else:
                print(presence_response[MESSAGE_TEXT])
                break

    def get_help_message(self):
        print(
            "help - вывод всех доступных комманд\n"
            "message - написать сообщение пользователю\n"
            "contacts - список контактов\n"
            "add_contact - добавить контакт\n"
            "del_contact - удалить контакт\n"
            "exit - выйти из программы\n"
        )


if __name__ == '__main__':
    client = Client()
    client.run_gui()
