from threading import Thread
from time import sleep

from lib2cubs.lowlevelcom import GenericConnection, Utils
from lib2cubs.lowlevelcom.frames import SimpleFrame


class ExampleClient(Thread):

	_host: str = None
	_port: int = None
	_pem_bundle_name: str = None
	is_running: bool = True
	connection: GenericConnection = None

	_is_ssl_disabled: bool = False

	@property
	def is_ssl_disabled(self):
		return self._is_ssl_disabled

	def __init__(self, pem_bundle_name: str, host: str = 'localhost', port: int = 60009,
				disable_ssl: bool = False,
				confirm_disabling_of_ssl: bool = False):
		super(ExampleClient, self).__init__()
		self._host = host
		self._port = port
		self._pem_bundle_name = pem_bundle_name
		self._is_ssl_disabled = disable_ssl and confirm_disabling_of_ssl

	@classmethod
	def event_connected(cls, event: str, connection: GenericConnection):
		# TODO  "this" and "event" maybe should be done as non-**kwargs arguments, but *args
		print(f'CONNECTED! {connection}')
		# print(f'{this} || {this.socket.version()}')

		for i in range(0, 5):
			sleep(2)
			command = f'Test {i}. It\'s just a text'
			print(f'Sending command: {command}')
			connection.send(SimpleFrame({
				'data': command
			}))
		connection.send(SimpleFrame({
			'action': 'exit',
		}))

	ii = False

	@classmethod
	def event_reading(cls, event: str, connection: GenericConnection, data):
		ref_class = Utils.frame_class_from_bytes(data)
		if ref_class:
			frame = ref_class.parse(data)
			content = frame.content
			print(f'Received reply from server: {content}')

			# if not cls.ii:
			# 	connection.disconnect(True)
			# 	cls.ii = True

	@classmethod
	def event_reconnect(cls, event: str, connection: GenericConnection):
		print("Reconnecting...")

	def run(self) -> None:
		GenericConnection.prepare_client(
			self._client_callback,
			self._pem_bundle_name,
			self._host, self._port,
			self._is_ssl_disabled
		)

	def _client_callback(self, cib):
		self.connection = GenericConnection.gen_new_client_connection(cib, {
			GenericConnection.EVENT_CONNECTED: self.event_connected,
			# GenericConnection.EVENT_DISCONNECT: self.event_disconnected,
			GenericConnection.EVENT_READING: self.event_reading,
			# GenericConnection.EVENT_RECONNECT: self.event_reconnect,
			# GenericConnection.EVENT_WRITING: event_writing,
		})
		# connection.is_auto_reconnect_allowed = True
		self.connection.wait_for_subroutines()
