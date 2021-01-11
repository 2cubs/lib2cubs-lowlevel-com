import socket
import ssl
from ssl import SSLSocket


class Connection:

	TYPE_CLIENT = 'client'
	TYPE_SERVER = 'server'
	# TYPE_SERVING_APP = 'serving-app'

	_type: str = None
	_socket: SSLSocket = None
	_host: str = None
	_port: int = None
	_is_reconnecting: bool = False
	_is_connected: bool = False
	_is_inited: bool = False

	#
	ssl_server_cert = None
	ssl_server_key = None
	ssl_client_cert = None
	ssl_client_key = None
	ssl_server_hostname = None

	def __init__(self, t: str, host: str = None, port: int = None, socket: SSLSocket = None, is_reconnecting: bool = False, is_connected: bool = False):
		self._type = t
		self._host = host
		self._host = host
		self._port = port
		self._socket = socket
		self._is_reconnecting = is_reconnecting
		self._is_connected = is_connected

	def _prepare_ssl_context(self):
		context = key = cert = ca_file = purpose = None
		if self._type == self.TYPE_SERVER:
			purpose = ssl.Purpose.CLIENT_AUTH
			ca_file = self.ssl_client_cert
			cert = self.ssl_server_cert
			key = self.ssl_server_key
		else:
			if self._type == self.TYPE_CLIENT:
				purpose = ssl.Purpose.SERVER_AUTH
				ca_file = self.ssl_server_cert
				cert = self.ssl_client_cert
				key = self.ssl_client_key

		if purpose is not None:
			context = ssl.create_default_context(purpose)
			context.verify_mode = ssl.CERT_REQUIRED
			context.load_verify_locations(cafile=ca_file)
			context.load_cert_chain(certfile=cert, keyfile=key)

		return context

	def init(self, reinit: bool = False):
		"""
		Init will workout only once if no parameter or False provided, so you can use it in a transparent way.
		For the re-init you have to specify True as an argument for the init() method. It will recreate socket
		:param reinit:
		:return:
		"""
		if reinit or not self._is_inited:
			self._is_inited = False
			self._create_socket(reinit)
			self._is_inited = True

	def _get_wrap_socket_params(self):
		if self._type == self.TYPE_SERVER:
			return {'server_side': True}
		if self._type == self.TYPE_CLIENT:
			return {'server_hostname': self.ssl_server_hostname}
		return {}

	def _create_socket(self, overwrite: bool = False):
		if overwrite or self._socket is None:
			if self._socket is not None:
				self._socket.close()
			self._socket = self._prepare_ssl_context().wrap_socket(self._prepare_socket(), **self._get_wrap_socket_params())

	def _prepare_socket(self) -> socket.socket:
		sock = socket.socket()
		if self._type == self.TYPE_SERVER:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		return sock

	def get_endpoint(self) -> tuple:
		return self._host, self._port

	def connect(self):
		"""
		Method is applicable only for a Client
		:return:
		"""
		if self._type != self.TYPE_CLIENT:
			raise Exception(f'You can\'t connect of this connection type [{self._type}].')

		# Initialisation
		self.init()
		# Connecting to the server
		self._socket.connect(self.get_endpoint())

	def listen(self):
		"""
		Method is applicable only for a Server
		:return:
		"""
		if self._type != self.TYPE_SERVER:
			raise Exception(f'You can\'t connect of this connection type [{self._type}].')

		# Initialisation
		self.init()
		# Listening and accepting connections
		self._socket.bind(self.get_endpoint())
		self._socket.listen()
