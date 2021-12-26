import ssl
from os.path import dirname, abspath, join


class Utils:

    _working_dir = None

    @classmethod
    def setup(cls, working_dir: str):
        cls.set_working_dir(working_dir)

    @classmethod
    def set_working_dir(cls, working_dir: str):
        cls._working_dir = working_dir

    @classmethod
    def get_working_dir(cls) -> str:
        return dirname(abspath(__file__)) if not cls._working_dir else cls._working_dir

    @classmethod
    def get_pem_file(cls, name: str, sub_path: str or list = 'ssl') -> str:
        return join(cls.get_working_dir(), join(sub_path), f'{name}-bundle.pem')

    @classmethod
    def get_server_socket_context(cls, name: str, sub_path: str or list = 'ssl') -> ssl.SSLContext:
        pem_file = cls.get_pem_file(name, sub_path)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # FIX   No cert check must be fixed
        context.verify_mode = ssl.CERT_NONE

        context.load_cert_chain(pem_file)

        return context
