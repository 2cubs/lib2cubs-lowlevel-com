import socket
import ssl
from threading import Thread
from time import sleep

from lib2cubs.lowlevelcom import GenericConnection, ConnInfoBlock


class ExampleClient(Thread):

	_host: str = None
	_port: int = None
	_pem_bundle_name: str = None
	is_running: bool = True
	connection: GenericConnection = None

	def __init__(self, pem_bundle_name: str, host: str = 'localhost', port: int = 60009):
		super(ExampleClient, self).__init__()
		self._host = host
		self._port = port
		self._pem_bundle_name = pem_bundle_name

	@classmethod
	def event_connected(cls, event: str, this: GenericConnection):
		# TODO  "this" and "event" maybe should be done as non-**kwargs arguments, but *args
		print(f'{this} || {this.socket.version()}')

		for i in range(0, 5):
			sleep(2)
			command = f'Test {i}. It\'s just a text'
			this.send(command.encode())
		this.send('#stop')

	@classmethod
	def event_reading(cls, event: str, this: GenericConnection, data):
		print(f'Received reply from server: {data}')

	def run(self) -> None:
		context = ssl.create_default_context()
		context.check_hostname = False
		context.verify_mode = ssl.CERT_NONE

		with socket.create_connection((self._host, self._port)) as sock:
			with context.wrap_socket(sock, server_hostname=self._host) as ssl_socket:
				cib = ConnInfoBlock.wrap_socket(ssl_socket, self._host, self._port)

				self.connection = GenericConnection(cib, {
					GenericConnection.EVENT_CONNECT: self.event_connected,
					# GenericConnection.EVENT_DISCONNECT: self.event_disconnected,
					GenericConnection.EVENT_READING: self.event_reading,
					# GenericConnection.EVENT_RECONNECT: self.event_reconnect,
					# GenericConnection.EVENT_WRITING: event_writing,
				})
				# connection.is_auto_reconnect_allowed = True
				self.connection.wait_for_subroutines()
