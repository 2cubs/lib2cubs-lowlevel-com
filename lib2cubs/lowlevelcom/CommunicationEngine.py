import socket
import ssl

from lib2cubs.lowlevelcom.basic import EngineFoundation, SimpleFrame


class CommunicationEngine(EngineFoundation):

	ssl_server_cert = None
	ssl_server_key = None
	ssl_client_cert = None
	ssl_client_key = None
	ssl_server_hostname = None

	@classmethod
	def example_server(cls, endpoint: str = '', port: int = 60009):
		print('Starting Server')
		s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((endpoint, port))
		s.listen()

		while True:
			conn, addr = s.accept()
			print(f"{addr} has connected")
			conn.send(bytes(SimpleFrame({'msg': 'Happy New Year 2021'})))
			conn.close()

	@classmethod
	def example_client(cls, endpoint: str = '127.0.0.1', port: int = 60009):
		print('Starting Client')
		s = socket.socket()
		s.connect((endpoint, port))
		data = SimpleFrame.parse(s.recv(1024)).content
		msg = data['msg']
		print(f'Received: {msg} | {data}')
		s.close()

	@classmethod
	def example_secure_server(cls, endpoint: str = '', port: int = 60009):

		context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
		context.verify_mode = ssl.CERT_REQUIRED
		context.load_cert_chain(certfile=cls.ssl_server_cert, keyfile=cls.ssl_server_key)
		context.load_verify_locations(cafile=cls.ssl_client_cert)
		# context.check_hostname = False
		print('Starting Secure Server (SSL)')
		s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((endpoint, port))
		s.listen()

		with context.wrap_socket(s, server_side=True) as ssock:
			while True:
				conn, addr = ssock.accept()
				print(f"{addr} has connected")
				conn.send(bytes(SimpleFrame({'msg': 'Happy New Year 2021'})))
				conn.close()

	@classmethod
	def example_secure_client(cls, endpoint: str = '127.0.0.1', port: int = 60009):

		context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=cls.ssl_server_cert)
		context.load_cert_chain(certfile=cls.ssl_client_cert, keyfile=cls.ssl_client_key)
		# context.check_hostname = False
		print('Starting Secure Client (SSL)')
		with socket.socket() as s:
			with context.wrap_socket(s, server_hostname=cls.ssl_server_hostname) as ssock:
				ssock.connect((endpoint, port))
				data = SimpleFrame.parse(ssock.recv(1024)).content
				msg = data['msg']
				print(f'Received: {msg} | {data}')

	@classmethod
	def prepare_ssl_content(cls):
		pass
