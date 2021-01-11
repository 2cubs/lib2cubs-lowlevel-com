import socket
import ssl
from ssl import SSLSocket, SSLContext
__author__ = "Ivan Ponomarev"
__email__ = "pi@spaf.dev"


class Connection:
	"""
	General connection object. Can be used bare or being extended in your app.
	"""

	TYPE_CLIENT = 'client'
	TYPE_SERVER = 'server'

	_type: str = None
	_socket: SSLSocket = None
	_host: str = None
	_port: int = None
	_is_reconnecting: bool = False
	_is_connected: bool = False
	_is_inited: bool = False

	# TODO Subject to revision
	ssl_server_cert = None
	ssl_server_key = None
	ssl_client_cert = None
	ssl_client_key = None
	ssl_server_hostname = None

	def __init__(self, t: str, host: str = None, port: int = None, sock: SSLSocket = None, is_reconnecting: bool = False, is_connected: bool = False):
		"""
		Constructor. Does not require to provide all the params.
		All the params except the very first one are optional.

		:param t: The type of connection
		:param host: Host
		:param port: Port
		:param sock: Secure Socket
		:param is_reconnecting: Can it reconnect in case of failure?
		:param is_connected: Is it already connected?
		"""
		self._type = t
		self._host = host
		self._host = host
		self._port = port
		self._socket = sock
		self._is_reconnecting = is_reconnecting
		self._is_connected = is_connected

	def _prepare_ssl_context(self) -> SSLContext:
		"""
		Preparing the SSL context needed to wrap the socket
		:return:
		"""
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

	def _get_wrap_socket_params(self) -> dict:
		"""
		Getting the correct params for SSL socket wrapping method.
		:return:
		"""
		if self._type == self.TYPE_SERVER:
			return {'server_side': True}
		if self._type == self.TYPE_CLIENT:
			return {'server_hostname': self.ssl_server_hostname}
		return {}

	def _create_socket(self, overwrite: bool = False):
		"""
		Generating/Regenerating SSL socket to be used further.
		:param overwrite: If True - would cause to recreating existing socket. Needed for reconnection
		:return:
		"""
		if overwrite or self._socket is None:
			if self._socket is not None:
				self._socket.close()
			self._socket = self._prepare_ssl_context().wrap_socket(self._prepare_socket(), **self._get_wrap_socket_params())

	def _prepare_socket(self) -> socket.socket:
		"""
		Just preparing socket. Might be more depending on type options applied.
		:return:
		"""
		sock = socket.socket()
		if self._type == self.TYPE_SERVER:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		return sock

	def get_endpoint(self) -> tuple:
		"""
		Returning the tuple of host and port. Just a common way to provide connecting/binding params.
		:return:
		"""
		return self._host, self._port

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

	def connect(self):
		"""
		Connecting to the server.
		Method is applicable only for a Client
		:return:
		"""
		if self._type != self.TYPE_CLIENT:
			raise Exception(f'You can\'t connect of this connection type [{self._type}].')

		# Initialisation
		self.init()
		# Connecting to the server
		self._socket.connect(self.get_endpoint())
		# TODO Method is not done.

	def listen(self):
		"""
		Binding and Listening for clients
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
		# TODO Method is not done.
