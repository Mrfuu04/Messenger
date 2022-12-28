import os
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QDialog, qApp

MAIN_FORM, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'auth.ui'))


class ClientAuth(QDialog, MAIN_FORM):

    def __init__(self):
        super(ClientAuth, self).__init__()
        self.ok_pressed = None
        self.setupUi(self)
        self._init_connects()

    def confirm(self):
        self.ok_pressed = True

    def cancel(self):
        self.ok_pressed = False
        sys.exit()

    def _init_connects(self):
        self.cancelBtn.clicked.connect(self.cancel)
        self.confirmBtn.clicked.connect(self.confirm)

