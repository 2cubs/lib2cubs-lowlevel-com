import logging
import ssl
from os.path import dirname, abspath, join

from lib2cubs.lowlevelcom.frames import EngineFoundation, SimpleFrame, AppFrame


class Utils:

    frames_references: dict = {
        EngineFoundation.AF_TYPE_1: SimpleFrame,
        # EngineFoundation.AF_TYPE_0:
    }

    _working_dir = None

    @classmethod
    def frame_class_from_bytes(cls, data: bytes):
        if not data:
            return None
        first_byte = data[0]
        af_type = int(first_byte >> 4)
        for ref_af_type, frame_class in cls.frames_references.items():
            if af_type == ref_af_type:
                return frame_class
        return None

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
        return join(cls.get_working_dir(), join(sub_path), f'{name}')

    @classmethod
    def get_server_socket_context(cls, name: str, sub_path: str or list = 'ssl') -> ssl.SSLContext:
        pem_file = cls.get_pem_file(name, sub_path)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        # FIX   No cert check must be fixed
        context.verify_mode = ssl.CERT_NONE

        # print("PEM File %s" % str(pem_file))
        context.load_cert_chain(pem_file)

        return context
