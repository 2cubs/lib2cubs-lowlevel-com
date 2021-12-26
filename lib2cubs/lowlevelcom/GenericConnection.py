import select
import ssl
import threading
from queue import Queue, Empty

from lib2cubs.lowlevelcom import ConnInfoBlock


class GenericConnection:

	EVENT_CONNECT = 'event-connect'
	EVENT_DISCONNECT = 'event-disconnect'
	EVENT_RECONNECT = 'event-reconnect'
	EVENT_READING = 'event-reading'
	EVENT_WRITING = 'event-writing'

	is_auto_reconnect_allowed: bool = False

	_events_list: tuple = (EVENT_CONNECT, EVENT_DISCONNECT, EVENT_RECONNECT, EVENT_READING, EVENT_WRITING)
	_event_callbacks: dict = None
	_events_queue: Queue = None

	_reading_data_queue: Queue = None
	_writing_data_queue: Queue = None

	_cib: ConnInfoBlock = None
	_sub_threads: list = None

	_is_latest_shutdown: bool = False
	_is_shutdown: bool = False

	_inputs: list = None
	_outputs: list = None

	def __init__(self, conn_info_block: ConnInfoBlock, event_callbacks: dict = None, run_events_thread: bool = True):
		self._sub_threads = []
		self._cib = conn_info_block
		self._events_queue = Queue()
		self._reading_data_queue = Queue()
		self._writing_data_queue = Queue()
		self._event_callbacks = event_callbacks if event_callbacks else {}

		if run_events_thread:
			t_el = threading.Thread(target=self.events_loop, name=f'{self._cib.name} Events Loop', args=(self, ))
			t_el.start()
			self._sub_threads.append(t_el)

		if self._cib.is_connected:
			self._trigger_event(self.EVENT_CONNECT)

		# TODO  Improve it at some point
		# FIX   Here is done improperly, redesign this part of the architecture urgently
		if run_events_thread:
			self._cib.socket.setblocking(False)

			t_sl = threading.Thread(target=self.select_loop, name=f'{self._cib.name} Select Loop', args=(self,))
			t_sl.start()
			self._sub_threads.append(t_sl)

	def send(self, data):
		if self.is_connected:
			self._writing_data_queue.put(data)

	def events_loop(self, *args):
		"""
		Main event loop
		The first parameter is "this" or "self", basically a self reference, in case if outer callable is used
		:param args:
		:return:
		"""
		while not self._is_latest_shutdown:
			if self._is_shutdown:
				self._is_latest_shutdown = True

			try:
				task = self._events_queue.get(timeout=5)
			except Empty:
				task = None
			if task:
				key = task[0]
				kwargs = task[1]
				cbk = self._event_callbacks[key] if key in self._event_callbacks else None
				if cbk:
					cbk(**kwargs, event=key, this=self)

	def select_loop(self, *args):
		self._inputs = inputs = [self._cib.socket, ]

		# NOTE  Contains select functionality only for WRITING
		t_writing = threading.Thread(target=self.write_loop, name=f'{self._cib.name} Writing Loop', args=(self,))
		t_writing.start()
		self._sub_threads.append(t_writing)

		# NOTE  Bellow is split functionality for READING
		t_reading = threading.Thread(target=self.read_loop, name=f'{self._cib.name} Reading Loop', args=(self,))
		t_reading.start()
		self._sub_threads.append(t_reading)

		while not self._is_shutdown:
			readable, _, exceptional = select.select(inputs, [], inputs, 5)

			for s in readable:
				# NOTE  Reading and operation
				# TODO  Reading/Writing Transport Protocols
				try:
					data = s.recv(1024)
				except ConnectionResetError as e:
					self._connection_shutdown(s, self.is_auto_reconnect_allowed)
				except ssl.SSLWantReadError as e:
					# TODO  Most likely the solution might cause problems. Revise!
					pass
				else:
					if data:
						self._reading_data_queue.put(data)
					else:
						# NOTE  Remote closing connection is happening here
						self._connection_shutdown(s, self.is_auto_reconnect_allowed)

			for s in exceptional:
				# NOTE  Exceptions/Errors and operation
				self._connection_shutdown(s, self.is_auto_reconnect_allowed)

	def write_loop(self, *args):
		self._outputs = outputs = [self._cib.socket, ]

		while not self._is_shutdown:
			try:
				data = self._writing_data_queue.get(timeout=5)
			except Empty:
				data = None

			if data:
				_, writable, exceptional = select.select([], outputs, outputs, 5)
				for s in writable:
					# NOTE  Writing and operation
					self._trigger_event(self.EVENT_WRITING, data=data)
					# TODO  Conversion!
					try:
						s.send(str(data).encode())
					except OSError as e:
						# NOTE  Connection is closed
						self._connection_shutdown(s, self.is_auto_reconnect_allowed)

				for s in exceptional:
					# NOTE  Exceptions/Errors and operation
					self._connection_shutdown(s, self.is_auto_reconnect_allowed)

	def read_loop(self, *args):
		while not self._is_shutdown:
			try:
				data = self._reading_data_queue.get(timeout=5)
			except Empty:
				data = None
			if data:
				self._trigger_event(self.EVENT_READING, data=data)

	def _check_event_key(self, key):
		if key not in self._events_list:
			# TODO  Implement custom exception
			raise Exception(f'Event with name "{key}" is not supported.')

	def _trigger_event(self, key: str, **kwargs):
		self._check_event_key(key)
		self._events_queue.put((key, kwargs))

	def set_event_callback(self, key: str, cbk: callable or None):
		self._check_event_key(key)
		self._event_callbacks[key] = cbk

	def get_event_callback(self, key: str) -> callable or None:
		self._check_event_key(key)
		return self._event_callbacks[key] if key in self._event_callbacks[key] else None

	@property
	def is_connected(self):
		return self._cib.is_connected and not self._is_shutdown

	@property
	def socket(self):
		return self._cib.socket

	def wait_for_subroutines(self):
		for t in self._sub_threads:
			t.join()
		self._sub_threads = []

	def disconnect(self):
		self._connection_shutdown(self._cib.socket, False)

	def _connection_shutdown(self, s, is_auto_reconnect: bool = False):
		if self._inputs and s in self._inputs:
			self._inputs.remove(s)
		if self._outputs and s in self._outputs:
			self._outputs.remove(s)
		self._is_shutdown = True
		self._cib.is_connected = False
		self._trigger_event(self.EVENT_DISCONNECT)
		if is_auto_reconnect:
			self._trigger_event(self.EVENT_RECONNECT)
