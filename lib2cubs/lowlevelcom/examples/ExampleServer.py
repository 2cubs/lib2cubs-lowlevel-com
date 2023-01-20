from threading import Thread

from lib2cubs.lowlevelcom import GenericConnection
from lib2cubs.lowlevelcom.BaseServerHandler import BaseServerHandler


class ExampleServer(Thread):

	name: str = 'Example Server (l2c-ll)'

	connection = None
	is_running = True

	_host: str = None
	_port: int = None
	_pem_bundle_name: str = None

	_is_ssl_disabled: bool = False

	_connection_threads = None

	@property
	def is_ssl_disabled(self):
		return self._is_ssl_disabled

	def __init__(self, pem_bundle_name: str, host: str = 'localhost', port: int = 60009,
				disable_ssl: bool = False,
				confirm_disabling_of_ssl: bool = False):
		super(ExampleServer, self).__init__()
		self._host = host
		self._port = port
		self._pem_bundle_name = pem_bundle_name
		self._is_ssl_disabled = disable_ssl and confirm_disabling_of_ssl
		self._connection_threads = []

	def run(self) -> None:

		GenericConnection.prepare_server(
			self._server_callback,
			self._pem_bundle_name,
			self._host, self._port,
			self._is_ssl_disabled
		)

		print('## ExampleServer: waiting for sub-threads to finish')
		for t in self._connection_threads:
			t.join()

	def _server_callback(self, sock):
		while self.is_running:
			handler = BaseServerHandler()
			g = GenericConnection.gen_new_server_connection(
				sock,
				{
					GenericConnection.EVENT_CONNECTED: handler.event_connected,
					GenericConnection.EVENT_DISCONNECTED: handler.event_disconnected,
					GenericConnection.EVENT_READING: handler.event_reading,
					GenericConnection.EVENT_BEFORE_RECONNECT: handler.event_before_reconnect,
					GenericConnection.EVENT_AFTER_RECONNECT: handler.event_after_reconnect,
					# GenericConnection.EVENT_WRITING: t.event_writing,
				}
			)
			for connection in g:
				if connection:
					handler.connection = connection
					self._connection_threads.append(handler)
					handler.start()
