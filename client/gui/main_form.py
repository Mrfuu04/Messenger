import os
import sys
from time import sleep

from PyQt5 import uic
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QBrush, QColor
from PyQt5.QtWidgets import QMainWindow, QMessageBox
from PyQt5.uic.properties import QtCore

from gui.add_contact import AddForm

MAIN_FORM, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'main_form.ui'))


class ClientGui(QMainWindow, MAIN_FORM):

    def __init__(self, transport):

        super(ClientGui, self).__init__()
        self.transport = transport
        self.chat_with = None

        self.red_color = QColor(255, 213, 213)
        self.green_color = QColor(204, 255, 204)
        self.grey_color = QColor(212, 212, 212)

        self.setupUi(self)
        self.initUi()
        self.message_show = QMessageBox()

        self.update_contact_list()

    def initUi(self):
        """Первичная инициализация всей формы"""
        # Инициализация списка контактов
        self.table_contacts_model = QStandardItemModel()
        self.contacts.setModel(self.table_contacts_model)
        self.contacts.horizontalHeader().hide()
        self.contacts.horizontalHeader().setStretchLastSection(True)
        self.contacts.verticalHeader().hide()
        self.contacts.doubleClicked.connect(self.__select_dialog_slot)

        # Инициализация истории сообщений
        self.messages_history_model = QStandardItemModel()
        self.messages.setModel(self.messages_history_model)
        self.messages.horizontalHeader().hide()
        self.messages.horizontalHeader().setStretchLastSection(True)
        self.messages.verticalHeader().hide()

        # Инициализация формы добавления пользователя
        self.add_contact_form = AddForm()
        self.add_contact_form.cancelBtn.clicked.connect(self.add_contact_form.close)
        self.add_contact_form.addBtn.clicked.connect(self.__add_contact_slot)

        # Сигналы на кнопки в основной форме
        self.addContact.clicked.connect(self.__add_contact_dialog_slot)
        self.delContact.clicked.connect(self.__delete_contact_slot)
        self.clearBtn.clicked.connect(self.__clear_message_input)
        self.sendBtn.clicked.connect(self.__send_message)

    def make_connection(self, transport_obj):
        """Связь сигналов обекта транспорта и своих слотов"""
        transport_obj.new_message.connect(self.__new_message_slot)
        transport_obj.connection_lost.connect(self.__connection_lost_slot)

    def update_contact_list(self):
        """Апдейт списка контактов"""
        self.table_contacts_model.clear()
        clients_dict = self.transport.get_contact_list()
        if clients_dict is not None:
            clients = clients_dict.get('msg_text')

            for client in clients:
                client_field = QStandardItem(client)
                client_field.setEditable(False)
                client_field.setBackground(QBrush(self.grey_color))
                self.table_contacts_model.appendRow(client_field)
        else:
            self.message_show.critical(
                self,
                'Внимание!',
                'Получен некорректный ответ от сервера '
                'при авторизации',
                self.message_show.Ok,
            )

    def update_chat_history(self, chat_with):
        """Апдейт истории сообщений"""
        self.messages_history_model.clear()
        username, messages = self.transport.get_chat_history(chat_with)
        for mes in messages:
            row = QStandardItem(f'{mes.date.replace(microsecond=0)}:\n {mes.message}')
            row.setEditable(False)

            if mes.sender == username:
                row.setBackground(QBrush(self.red_color))
                row.setTextAlignment(Qt.AlignRight)
            else:
                row.setBackground(QBrush(self.green_color))
                row.setTextAlignment(Qt.AlignLeft)

            self.messages_history_model.appendRow(row)

        self.messages.scrollToBottom()

    # --- Слоты --- #

    def __add_contact_dialog_slot(self):
        self.add_contact_form.show()

    def __add_contact_slot(self):
        add_contact_name = self.add_contact_form.username.text()
        response = self.transport.add_contact(add_contact_name)
        self.message_show.question(
            self,
            '...',
            response,
            self.message_show.Ok,
        )
        self.update_contact_list()
        self.add_contact_form.close()

    def __delete_contact_slot(self):
        if not self.contacts.selectionModel().hasSelection():
            self.message_show.question(
                self,
                '...',
                'Для удаления пользователя выберите его в списке',
                self.message_show.Ok,
            )
            return

        delete_contact_name = self.contacts.currentIndex().data()
        if self.message_show.question(self,
                                    'Удаление',
                                    f'Контакт {delete_contact_name} будет удален',
                                    QMessageBox.Yes,
                                    QMessageBox.No) == QMessageBox.No:
            return

        response = self.transport.del_contact(delete_contact_name)
        self.message_show.question(
            self,
            '...',
            response,
            self.message_show.Ok,
        )
        self.update_contact_list()

    def __select_dialog_slot(self):
        if self.contacts.currentIndex().isValid():
            self.chat_with = self.contacts.currentIndex().data()
            chatter_in_table = self.table_contacts_model.itemFromIndex(
                self.contacts.currentIndex())
            chatter_in_table.setBackground(QBrush(self.grey_color))
            self.chatWithLabel.setText(f'Чат с {self.chat_with}')

            self.messages.setDisabled(False)
            self.messageInput.setDisabled(False)
            self.sendBtn.setDisabled(False)
            self.clearBtn.setDisabled(False)

            self.update_chat_history(self.chat_with)

    @pyqtSlot(str)
    def __new_message_slot(self, sender):
        """Слот получения нового сообщения"""
        if sender == self.chat_with:
            self.update_chat_history(sender)
        else:
            find_contacts = self.table_contacts_model.findItems(sender)
            if find_contacts:
                find_contacts[0].setBackground(QBrush(self.green_color))
            else:
                add_contact = QStandardItem(sender)
                add_contact.setEditable(False)
                add_contact.setBackground(QBrush(self.red_color))
                self.table_contacts_model.appendRow([add_contact])

    @pyqtSlot()
    def __connection_lost_slot(self):
        """Слот потери связи с сервером"""
        self.message_show.critical(
            self,
            'Внимание',
            'Сбой соединения с сервером!',
            self.message_show.Ok,
        )
        self.close()

    def closeEvent(self, a0):
        self.transport.send_exit_message()
        super(ClientGui, self).closeEvent(a0)

    def __clear_message_input(self):
        self.messageInput.setText('')

    def __send_message(self):
        recipient = self.contacts.currentIndex().data()
        msg_text = self.messageInput.toPlainText()

        self.transport.send_message(recipient, msg_text)
        self.update_chat_history(recipient)
        self.__clear_message_input()

    # --- Конец слотов --- #
