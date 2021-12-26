import select
import socket
import threading
from datetime import datetime
from threading import Thread

from lib2cubs.lowlevelcom import ConnInfoBlock, GenericConnection, Utils


class ExampleServer(Thread):

	name: str = 'Example Server (l2c-ll)'

	connection = None
	is_running = True

	_host: str = None
	_port: int = None
	_pem_bundle_name: str = None

	def __init__(self, pem_bundle_name: str, host: str = 'localhost', port: int = 60009):
		super(ExampleServer, self).__init__()
		self._host = host
		self._port = port
		self._pem_bundle_name = pem_bundle_name

	def event_reconnect(self, event, this: GenericConnection):
		print(f'OOPS. Reconnect event, what to do?! {this._cib}')

	def event_writing(self, event, this: GenericConnection, data):
		print(f'Writing of data: {data}')

	def event_reading(self, event, this: GenericConnection, data):
		print(f'Received: {data}')
		ts = datetime.now()
		reply = f'ECHO({data.decode()}) /{ts}/'
		print(f'Sending back: {reply}')
		this.send(reply)

	def event_connected(self, event, this):
		print(str(this._cib))

	def event_disconnected(self, event, this):
		print(str(this._cib))

	def t_app_server(self, cib: ConnInfoBlock):
		print(f'App started for {cib}')
		self.connection = GenericConnection(cib, {
			GenericConnection.EVENT_CONNECT: self.event_connected,
			GenericConnection.EVENT_DISCONNECT: self.event_disconnected,
			GenericConnection.EVENT_READING: self.event_reading,
			GenericConnection.EVENT_RECONNECT: self.event_reconnect,
			# GenericConnection.EVENT_WRITING: event_writing,
		})
		# connection.is_auto_reconnect_allowed = True
		self.connection.wait_for_subroutines()

	def run(self) -> None:
		context = Utils.get_server_socket_context(self._pem_bundle_name)

		sub_threads = []

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.bind((self._host, self._port))
			sock.listen(5)

			with context.wrap_socket(sock, server_side=True) as ssl_sock:
				read_list = [ssl_sock, ]

				print('## Waiting')
				while self.is_running:
					readable, _, exceptional = select.select(read_list, [], [], 5)
					for s in readable:
						cib = ConnInfoBlock.from_accept(s.accept())

						t_as = threading.Thread(
							name=f'App {cib.name}',
							target=self.t_app_server,
							args=(cib,)
						)
						sub_threads.append(t_as)
						t_as.start()

		print('## ExampleServer: waiting for sub-threads to finish')
		for t in sub_threads:
			t.join()
