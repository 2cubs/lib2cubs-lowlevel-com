import socket
import ssl
from ssl import SSLSocket, SSLContext, SSLError, SSLWantReadError

from lib2cubs.lowlevelcom.basic import SimpleFrame
from lib2cubs.lowlevelcom.exceptions import SecurityError
from lib2cubs.lowlevelcom.ssl import SSLInfoContainer


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
	_is_blocking: bool = False

	_bf_frame_form = None
	_bf_bytes_form: bytearray = None
	_bf_msg_len_expected: int = 1
	_bf_szofsz: int = None
	_bf_step_completed_1: bool = False
	_bf_step_completed_2: bool = False

	ssl_info: SSLInfoContainer = None

	# def __init__(self, t: str, host: str = None, port: int = None, sock: SSLSocket = None, is_connected: bool = False, is_reconnecting: bool = None):
	def __init__(self, connection_type: str, host: str = None, port: int = None,
				ssl_info: SSLInfoContainer or None or False = None):

		self.ssl_info = ssl_info

		self._type = connection_type
		self._host = host
		self._port = port
		# self._socket = sock
		# self._is_reconnecting = is_reconnecting if is_reconnecting is not None else t == self.TYPE_CLIENT
		# self._is_connected = is_connected
		self._bf_bytes_form = bytearray()
		# if self._is_connected:
		# 	self._after_open_connection()

	@property
	def is_ssl_disabled(self):
		return self.ssl_info is False

	@property
	def is_ssl_provided(self):
		return bool(self.ssl_info)

	def check_if_ready_to_connect(self):
		if self.ssl_info is None:
			raise SecurityError('ssl_info parameter is not filled. If you are sure you want to '
								'skip encryption (Which is the worst idea ever!) - then specify "False" '
								'to disable this exception (again, please don\'t do that!)')

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
			if not ca_file or not cert or not key:
				raise Exception('At least one of ca_file, cert or key is not specified.')
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
		Generating/Regenerating SSL/Normal socket to be used further.
		:param overwrite: If True - would cause to recreating existing socket. Needed for reconnection
		:return:
		"""
		if overwrite or self._socket is None:
			if self._socket is not None:
				self._socket.close()
			if not self.is_ssl_disabled:
				self._socket = self._prepare_ssl_context().wrap_socket(self._prepare_socket(), **self._get_wrap_socket_params())
			else:
				self._socket = self._prepare_socket()

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

	@property
	def is_connected(self):
		return self._is_connected

	def init(self, reinit: bool = False):
		"""
		Init will workout only once if no parameter or False provided, so you can use it in a transparent way.
		For the re-init you have to specify True as an argument for the init() method. It will recreate socket
		:param reinit:
		:return:
		"""
		self.check_if_ready_to_connect()

		if reinit or not self._is_inited:
			self._is_inited = False
			self._create_socket(reinit)
			self._is_inited = True

	@property
	def is_blocking_allowed(self):
		return self._is_blocking

	@is_blocking_allowed.setter
	def is_blocking_allowed(self, val):
		self._is_blocking = bool(val)

	def _after_open_connection(self):
		self._socket.setblocking(self._is_blocking)

	def connect(self, recreate: bool = False):
		"""
		Connecting to the server.
		Method is applicable only for a Client
		:return:
		"""
		if self._type != self.TYPE_CLIENT:
			raise Exception(f'You can\'t connect for this connection type [{self._type}].')

		# Initialisation
		self.init(recreate)
		# Connecting to the server
		self._socket.connect(self.get_endpoint())
		self._is_connected = True
		self._after_open_connection()

	def listen(self):
		"""
		Binding and Listening for clients
		Method is applicable only for a Server
		:return:
		"""
		if self._type != self.TYPE_SERVER:
			raise Exception(f'You can\'t listen on this connection type [{self._type}].')

		# Initialisation
		self.init()
		# Listening and accepting connections
		self._socket.bind(self.get_endpoint())
		self._socket.listen()
		self._after_open_connection()

	@property
	def host(self):
		return self._host

	@property
	def port(self):
		return self._port

	def set_connection_info(self, sock, is_connected: bool = False, run_after_open_event: bool = True):
		self._socket = sock
		self._is_connected = is_connected
		if run_after_open_event:
			self._after_open_connection()

	def make_child(self, t, sock, host, port):
		child_connection = self.__class__(t, host, port)
		child_connection.set_connection_info(sock, True)
		return child_connection

	def accept(self, t: str = ''):
		sock, addr = self._socket.accept()
		return self.make_child(t, sock, addr[0], addr[1])

	def get_last_received_frame(self):
		if self._bf_frame_form and self._bf_frame_form.is_construction_completed():
			return self._bf_frame_form
		return None

	def send_frame(self, frame):
		try:
			self._socket.send(bytes(frame))
		except OSError as e:
			print('Can\'t write to the socket')

	def collect_frame(self):
		frame = None
		try:
			frame = self._gather_frame_from_socket(SimpleFrame)
			if frame is None:
				print('Exited')
		except SSLWantReadError as e:
			# todo move to ll
			pass

		if isinstance(frame, SimpleFrame):
			return frame

		return False

	def _receive_chunk(self):
		len_diff = self._bf_msg_len_expected - len(self._bf_bytes_form)
		if len_diff > 0:
			try:
				b = self._socket.recv(len_diff)
				if not b:
					self._connection_is_closed()
					return None
				self._bf_bytes_form += b
			except (SSLError, ConnectionResetError, OverflowError, MemoryError) as e:
				if ('reason' in e.__dict__ and e.reason is not None) or isinstance(e, MemoryError) or isinstance(e, ConnectionResetError) or isinstance(e, OverflowError):
					print(f'Reconnect is needed: {e}')
					self._connection_is_closed()
					return None
				# 	Operation did not complete can happen here, so do not break the connection
			except BlockingIOError as e:
				pass
			except OSError as e:
				print('Can\'t read from the socket')
		return True

	def _connection_is_closed(self):
		self._is_connected = False
		self._socket.close()
		print('Has disconnected')

	def _gather_frame_from_socket(self, frame_class):
		if not self._receive_chunk():
			return None

		# Step 1
		if len(self._bf_bytes_form) == 1:
			# Getting size of the size and increasing the expected length
			self._bf_szofsz = int(int.from_bytes(self._bf_bytes_form, 'big') & 0x0F)
			self._bf_msg_len_expected = self._bf_szofsz + 1
			self._bf_step_completed_1 = True
			if not self._receive_chunk():
				return None

		# Step 2
		if self._bf_szofsz is not None and len(self._bf_bytes_form) == (self._bf_szofsz + 1):
			# Getting size of the content and increasing the expected length
			self._bf_msg_len_expected = int.from_bytes(self._bf_bytes_form[1:], 'big') + self._bf_szofsz + 1
			self._bf_step_completed_2 = True
			if not self._receive_chunk():
				return None

		# Step 3
		if self._bf_step_completed_1 and self._bf_step_completed_2 and len(self._bf_bytes_form) == self._bf_msg_len_expected:
			# Received all the data, and making frame from it
			self._bf_msg_len_expected = 1
			self._bf_step_completed_1 = self._bf_step_completed_2 = False
			try:
				self._bf_frame_form = frame_class.parse(self._bf_bytes_form)
			except ValueError as e:
				print(f'Reconnect is needed: {e}')
				self._connection_is_closed()
				return None
			self._bf_bytes_form = bytearray()
			return self._bf_frame_form

		return True
