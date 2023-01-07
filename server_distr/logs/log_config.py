import os
import logging


client_log = logging.getLogger('server')
formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(module)-10s %(message)s')

file_name = os.path.dirname(os.path.abspath(__file__))
file_name = os.path.join(file_name, 'server.log')

file_hand = logging.FileHandler(file_name, encoding='utf-8')
file_hand.setLevel(logging.DEBUG)
file_hand.setFormatter(formatter)

if not client_log.handlers:
    client_log.addHandler(file_hand)
client_log.setLevel(logging.INFO)
