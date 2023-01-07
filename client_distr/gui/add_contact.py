import os
from PyQt5 import uic
from PyQt5.QtWidgets import QDialog

MAIN_FORM, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'add_contact.ui'))


class AddForm(QDialog, MAIN_FORM):
    def __init__(self):
        super(AddForm, self).__init__()
        self.setupUi(self)
