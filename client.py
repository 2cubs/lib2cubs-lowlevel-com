from os.path import dirname, abspath

from lib2cubs.lowlevelcom import Utils
from lib2cubs.lowlevelcom.examples import ExampleClient

Utils.setup(dirname(abspath(__file__)))


host = 'localhost'
port = 60009


if __name__ == '__main__':
    try:
        server = ExampleClient('kokoko', host, port)
        server.start()
        server.join()
    except (KeyboardInterrupt, SystemExit):
        print('## [ctrl+c] pressed')
        print('## Out of the app.')
        server.is_running = False

        if server.connection:
            server.connection.disconnect()
            print('## Waiting for all sub-routines to finish up.')
