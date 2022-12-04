import os
import subprocess
import argparse
import sys
from time import sleep


PYTHON_PATH = sys.executable
BASE_PATH = os.path.dirname(os.path.abspath(__file__))


def get_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        '-c',
        '--clients',
        type=int,
        help='Количество запускаемых клиентов',
        default=1,
    )
    args = arg_parser.parse_args()

    return args


def get_subprocess(executable):
    return subprocess.Popen(f'{PYTHON_PATH} {BASE_PATH}/{executable}',
                            creationflags=subprocess.CREATE_NEW_CONSOLE)


def main():
    # subprocess.Popen(f'{PYTHON_PATH} {BASE_PATH}/{"server/server.py"}',)
    PROCESSES = []
    args = get_args()
    PROCESSES.append(get_subprocess('server/server.py'))
    for i in range(args.clients):
        sleep(0.5)
        PROCESSES.append(get_subprocess('client/client.py'))


if __name__ == '__main__':
    main()
