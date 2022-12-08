import os

# ---- SERVER SETTINGS ---- #
SERVER_MAX_LISTEN = 5
SERVER_SETTIMEOUT = 1
MAX_PACKAGE_SIZE = 1024
ENCODING = 'utf-8'
DB_NAME = 'server_db'
DB_PATH = os.path.join(
    os.sep.join(
        os.path.abspath(
            os.getcwd()).split(os.sep)), 'server_db')

# ---- JIM VARIABLES ---- #
ACTION = 'action'
TIME = 'time'
USER = 'user'
SENDER = 'from'
DESTINATION = 'to'
MESSAGE = 'msg'
MESSAGE_TEXT = 'msg_text'

# ---- JIM+ VARIABLES ---- #
SERVER = 'server'
ACCOUNT_NAME = 'account_name'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
EXIT = 'exit'
CONTACTS = 'get_contacts'
ADD_CONTACT = 'add_contact'
DEL_CONTACT = 'del_contact'

# ---- RESPONSES ---- #
RESPONSE_200 = {
    RESPONSE: '200',
    MESSAGE_TEXT: None,
    SENDER: SERVER,
}
RESPONSE_400 = {
    RESPONSE: '400',
    MESSAGE_TEXT: None,
    SENDER: SERVER,
}
RESPONSE_201 = {
    RESPONSE: '201',
    MESSAGE_TEXT: "Имя уже используется",
    SENDER: SERVER,
}