from lib2cubs.lowlevelcom.basic import EngineFoundation, SimpleFrame


class CommunicationEngine(EngineFoundation):

	@classmethod
	def example_server(cls, endpoint: str = '', port: int = 60009):
		print('Starting Server')
		sock = cls.prepare_socket(cls.TYPE_SERVER, endpoint, port)

		while True:
			conn, addr = sock.accept()
			print(f"{addr} has connected")
			conn.send(bytes(SimpleFrame({'msg': 'Happy New Year 2021'})))
			conn.close()

		sock.close()

	@classmethod
	def example_client(cls, endpoint: str = '127.0.0.1', port: int = 60009):
		print('Starting Client')
		sock = cls.prepare_socket(cls.TYPE_CLIENT, endpoint, port)

		data = SimpleFrame.parse(sock.recv(1024)).content
		msg = data['msg']
		print(f'Received: {msg} | {data}')

		sock.close()

	@classmethod
	def example_secure_server(cls, endpoint: str = '', port: int = 60009):

		print('Starting Secure Server (SSL)')
		t = cls.TYPE_SERVER
		context = cls.prepare_ssl_context(t)
		sock = cls.prepare_socket(t, endpoint, port)

		with context.wrap_socket(sock, server_side=True) as secure_sock:
			while True:
				conn, addr = secure_sock.accept()
				print(f"{addr} has connected")
				conn.send(bytes(SimpleFrame({'msg': 'Happy New Year 2021'})))
				conn.close()

		sock.close()

	@classmethod
	def example_secure_client(cls, endpoint: str = '127.0.0.1', port: int = 60009):
		t = cls.TYPE_CLIENT
		context = cls.prepare_ssl_context(t)
		sock = cls.prepare_socket(t, endpoint, port)

		print('Starting Secure Client (SSL)')
		with context.wrap_socket(sock, server_hostname=cls.ssl_server_hostname) as secure_sock:
			secure_sock.connect((endpoint, port))
			data = SimpleFrame.parse(secure_sock.recv(1024)).content
			msg = data['msg']
			print(f'Received: {msg} | {data}')

		sock.close()

	@classmethod
	def secure_server(cls, cb: callable, endpoint: str = '', port: int = 60009):
		t = cls.TYPE_SERVER
		context = cls.prepare_ssl_context(t)

		with cls.prepare_socket(t, endpoint, port) as sock:
			with context.wrap_socket(sock, server_side=True) as secure_sock:
				# secure_sock.setblocking(False)
				cb(secure_sock)
				# while True:
				# 	conn, addr = secure_sock.accept()
				# 	cb(conn)
				# 	conn.close()

	@classmethod
	def secure_client(cls, cb: callable, endpoint: str = '127.0.0.1', port: int = 60009):
		t = cls.TYPE_CLIENT
		context = cls.prepare_ssl_context(t)

		with cls.prepare_socket(t, endpoint, port) as sock:
			with context.wrap_socket(sock, server_hostname=cls.ssl_server_hostname) as secure_sock:
				secure_sock.connect((endpoint, port))
				# secure_sock.setblocking(False)
				cb(secure_sock)
