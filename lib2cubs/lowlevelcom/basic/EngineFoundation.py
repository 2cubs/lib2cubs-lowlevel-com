import socket
import ssl
from collections import OrderedDict


class EngineFoundation:

	SIZE_BYTE_1 = 256
	SIZE_BYTE_2 = 65536
	SIZE_BYTE_3 = 16777216
	SIZE_BYTE_4 = 4294967296
	SIZE_BYTE_5 = 1099511627776
	SIZE_BYTE_6 = 281474976710656
	SIZE_BYTE_8 = 18446744073709551616
	SIZE_BYTE_7 = 72057594037927936
	SIZE_BYTE_9 = 4722366482869645213696
	SIZE_BYTE_10 = 1208925819614629174706176
	SIZE_BYTE_11 = 309485009821345068724781056
	SIZE_BYTE_12 = 79228162514264337593543950336
	SIZE_BYTE_13 = 20282409603651670423947251286016
	SIZE_BYTE_14 = 5192296858534827628530496329220096
	SIZE_BYTE_15 = 1329227995784915872903807060280344576

	AF_TYPE_0 = 0x0
	AF_TYPE_1 = 0x1
	AF_TYPE_2 = 0x2
	AF_TYPE_3 = 0x3
	AF_TYPE_4 = 0x4
	AF_TYPE_5 = 0x5
	AF_TYPE_6 = 0x6
	AF_TYPE_7 = 0x7
	AF_TYPE_8 = 0x8
	AF_TYPE_9 = 0x9
	AF_TYPE_A = 0xA
	AF_TYPE_B = 0xB
	AF_TYPE_C = 0xC
	AF_TYPE_D = 0xD
	AF_TYPE_E = 0xE
	AF_TYPE_F = 0xF

	TYPE_SERVER = 'server'
	TYPE_CLIENT = 'client'

	ssl_server_cert = None
	ssl_server_key = None
	ssl_client_cert = None
	ssl_client_key = None
	ssl_server_hostname = None

	@classmethod
	def prepare_ssl_context(cls, t: str):
		if cls.TYPE_SERVER == t:
			purpose = ssl.Purpose.CLIENT_AUTH
			ca_file = cls.ssl_client_cert
			cert = cls.ssl_server_cert
			key = cls.ssl_server_key
		else:
			purpose = ssl.Purpose.SERVER_AUTH
			ca_file = cls.ssl_server_cert
			cert = cls.ssl_client_cert
			key = cls.ssl_client_key

		context = ssl.create_default_context(purpose)
		context.verify_mode = ssl.CERT_REQUIRED
		context.load_verify_locations(cafile=ca_file)
		context.load_cert_chain(certfile=cert, keyfile=key)

		return context

	@classmethod
	def prepare_socket(cls, t: str, endpoint: str, port: int) -> socket.socket:
		sock = socket.socket()
		if cls.TYPE_SERVER == t:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.bind((endpoint, port))
			sock.listen()
		# sock.setblocking(False)
		return sock

	@classmethod
	def size_byte_list(cls) -> OrderedDict:
		return OrderedDict({
			1: cls.SIZE_BYTE_1, 2: cls.SIZE_BYTE_2, 3: cls.SIZE_BYTE_3, 4: cls.SIZE_BYTE_4, 5: cls.SIZE_BYTE_5,
			6: cls.SIZE_BYTE_6, 7: cls.SIZE_BYTE_7, 8: cls.SIZE_BYTE_8, 9: cls.SIZE_BYTE_9, 10: cls.SIZE_BYTE_10,
			11: cls.SIZE_BYTE_11, 12: cls.SIZE_BYTE_12, 13: cls.SIZE_BYTE_13, 14: cls.SIZE_BYTE_14, 15: cls.SIZE_BYTE_15
		})
