from ssl import SSLSocket


class ConnInfoBlock:

	_socket: SSLSocket = None

	_host: str = None
	_port: int = None
	_is_connected: bool = False

	def __init__(self, socket: SSLSocket, host: str, port: int, is_connected: bool):
		self._socket = socket
		self._host = host
		self._port = port
		self._is_connected = is_connected

	@property
	def socket(self):
		return self._socket

	@property
	def host(self):
		return self._host

	@property
	def port(self):
		return self._port

	@property
	def is_connected(self):
		return self._is_connected

	@is_connected.setter
	def is_connected(self, val: bool):
		self._is_connected = val
		self.socket.close()

	@property
	def name(self):
		return f'{self.host}:{self.port}'

	@classmethod
	def from_accept(cls, data: list):
		sock = data[0]
		host, port = data[1]
		return cls(sock, host, port, is_connected=True)

	@classmethod
	def wrap_socket(cls, sock, host, port):
		return cls(sock, host, port, is_connected=True)

	def __str__(self):
		is_connected = 'connected' if self.is_connected else 'not connected'
		return f'ConnInfoBlock[{self.name}] / {is_connected}'
