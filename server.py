from os.path import dirname, abspath

from lib2cubs.lowlevelcom import Utils
from lib2cubs.lowlevelcom.examples import ExampleServer

Utils.setup(dirname(abspath(__file__)))


host = 'localhost'
port = 60009

disable_ssl = False


if __name__ == '__main__':
    try:
        server = ExampleServer('kokoko-bundle.pem', host, port,
                               disable_ssl=disable_ssl, confirm_disabling_of_ssl=disable_ssl)
        server.start()
        server.join()
    except (KeyboardInterrupt, SystemExit):
        print('## [ctrl+c] pressed')
        print('## Out of the app.')
        server.is_running = False

        if server.connection:
            server.connection.disconnect()
            print('## Waiting for all sub-routines to finish up.')
