import os
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, qApp

from gui.register import ClientRegisterUI


MAIN_FORM, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'auth.ui'))


class ClientAuth(QDialog, MAIN_FORM):

    def __init__(self):
        super(ClientAuth, self).__init__()
        self.ok_pressed = None
        self.setupUi(self)
        self.register_form = ClientRegisterUI()
        self.init_signals()

    def init_signals(self):
        self.cancelBtn.clicked.connect(self._cancel_slot)
        self.confirmBtn.clicked.connect(self._confirm_slot)
        self.registerBtn.clicked.connect(self._register_slot)

    def _confirm_slot(self):
        self.ok_pressed = True

    def _cancel_slot(self):
        self.ok_pressed = False
        sys.exit()

    def _register_slot(self):
        self.register_form.show()
