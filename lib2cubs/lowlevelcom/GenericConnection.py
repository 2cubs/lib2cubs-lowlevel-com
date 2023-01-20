import logging
import select
import socket
import ssl
import threading
from queue import Queue, Empty
from ssl import SSLSocket
from threading import Thread, Lock
from typing import Generator

from lib2cubs.lowlevelcom import ConnInfoBlock, Utils
from lib2cubs.lowlevelcom.frames import SimpleFrame, AppFrame


class GenericConnection:

	EVENT_CONNECTED = 'event-connected'

	EVENT_DISCONNECTED = 'event-disconnected'

	EVENT_BEFORE_RECONNECT = 'event-before-reconnect'
	EVENT_AFTER_RECONNECT = 'event-after-reconnect'

	EVENT_READING = 'event-reading'
	EVENT_WRITING = 'event-writing'

	is_auto_reconnect_allowed: bool = False

	_events_list: tuple = (
		EVENT_CONNECTED,
		EVENT_DISCONNECTED,
		EVENT_BEFORE_RECONNECT, EVENT_AFTER_RECONNECT,
		EVENT_READING, EVENT_WRITING
	)

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

	_writing_lock: Lock = None
	_reading_lock: Lock = None

	def __init__(self, conn_info_block: ConnInfoBlock, event_callbacks: dict = None, run_events_thread: bool = True):
		self._sub_threads = []
		self._cib = conn_info_block
		self._events_queue = Queue()
		self._reading_data_queue = Queue()
		self._writing_data_queue = Queue()
		self._event_callbacks = event_callbacks if event_callbacks else {}
		self._writing_lock = Lock()
		self._reading_lock = Lock()

		if run_events_thread:
			t_el = threading.Thread(target=self.events_loop, name=f'{self._cib.name} Events Loop', args=(self, ))
			t_el.start()
			self._sub_threads.append(t_el)

		if self._cib.is_connected:
			self._trigger_event(self.EVENT_CONNECTED, connection=self)

		# TODO  Improve it at some point
		# FIX   Here is done improperly, redesign this part of the architecture urgently
		if run_events_thread:
			self._cib.socket.setblocking(False)

			t_sl = threading.Thread(target=self.select_loop, name=f'{self._cib.name} Select Loop', args=(self,))
			t_sl.start()
			self._sub_threads.append(t_sl)

	def send(self, data):
		# if self.is_connected:
		logging.debug('Adding data to a writing-queue')
		self._writing_data_queue.put(data)

	def events_loop(self, *args):
		"""
		Main event loop
		The first parameter is "this" or "self", basically a self reference, in case if outer callable is used
		:param args:
		:return:
		"""
		sub_threads = []
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
					t = Thread(target=cbk, kwargs={**kwargs, 'event': key, 'connection': self})
					# cbk(**kwargs, event=key, this=self)
					t.start()
					sub_threads.append(t)

		for t in sub_threads:
			logging.debug('Waiting 30 seconds for sub-threads to complete')
			t.join(timeout=30)

	def prepare_af_structures(self, first_byte: int):
		af_type = int(first_byte >> 4)
		szofsz = int(first_byte & 0x0F)

		app_frame_class = None
		# TODO  Implement and Extend registry for AppFrame types choosing
		if af_type == SimpleFrame.AF_TYPE:
			app_frame_class = SimpleFrame

		return szofsz, app_frame_class

	def select_loop(self, *args):
		self._inputs = inputs = [self._cib.socket, ]

		# NOTE  Contains select functionality only for WRITING
		t_writing = threading.Thread(target=self.write_loop, name=f'{self._cib.name} Writing Loop', args=(self,))
		t_writing.start()
		logging.debug('Write-loop thread has been started')
		self._sub_threads.append(t_writing)

		# NOTE  Bellow is split functionality for READING
		t_reading = threading.Thread(target=self.read_loop, name=f'{self._cib.name} Reading Loop', args=(self,))
		t_reading.start()
		logging.debug('Read-loop thread has been started')
		self._sub_threads.append(t_reading)

		while not self._is_shutdown:
			readable, _, exceptional = select.select(inputs, [], inputs, 5)

			for s in readable:
				# NOTE  Reading and operation
				# TODO  Reading/Writing Transport Protocols
				is_connection_closed = False
				try:
					logging.debug(f'Acquiring reading lock')
					self._reading_lock.acquire(True, 5)

					first_byte = s.recv(1)
					if len(first_byte) > 0:

						szofsz, app_frame_class = self.prepare_af_structures(first_byte[0])
						size_to_read = int(s.recv(szofsz)[0])
						payload = s.recv(size_to_read)

						frame = app_frame_class(payload=payload)
					else:
						is_connection_closed = True

				except ssl.SSLWantReadError as e:
					# TODO  Improve through reiteration
					pass
				except BlockingIOError as e:
					logging.error('BlockingIOError Select-loop Error has happened: %s', e)
				except (ConnectionResetError, OSError) as e:
					logging.debug('Select-loop exception occurred: %s', e)
					self._connection_shutdown(s, self.is_auto_reconnect_allowed)
				else:
					if not is_connection_closed:
						self._reading_data_queue.put(frame)
					else:
						# NOTE  Remote closing connection is happening here
						self._connection_shutdown(s, self.is_auto_reconnect_allowed)
				finally:
					logging.debug(f'Releasing reading lock')
					self._reading_lock.release()

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
				try:
					_, writable, exceptional = select.select([], outputs, outputs, 5)
				except OSError as e:
					writable = []
					exceptional = []
					logging.error('Write-loop Error happened: %s', e)

				for s in writable:
					# NOTE  Writing and operation
					self._trigger_event(self.EVENT_WRITING, data=data, connection=self)
					# TODO  Conversion!
					try:
						logging.debug(f'Acquiring writing lock')
						self._writing_lock.acquire()
						s.send(bytes(data))
					except OSError as e:
						# NOTE  Connection is closed
						logging.error('Error has happened: %s', e)
						self._connection_shutdown(s, self.is_auto_reconnect_allowed)
					finally:
						logging.debug(f'Releasing writing lock')
						self._writing_lock.release()

				for s in exceptional:
					# NOTE  Exceptions/Errors and operation
					self._connection_shutdown(s, self.is_auto_reconnect_allowed)

	def read_loop(self, *args):
		while not self._is_shutdown:
			try:
				frame = self._reading_data_queue.get(timeout=5)
			except Empty:
				frame = None
			if frame:
				self._trigger_event(self.EVENT_READING, frame=frame)

	def _check_event_key(self, key):
		if key not in self._events_list:
			# TODO  Implement custom exception
			logging.error('Event with name "%s" is not supported', key)

	def _trigger_event(self, key: str, **kwargs):
		logging.debug('Triggered an event %s', key)
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
		logging.debug('Waiting for GenericConnection Sub-Routines')

		for t in self._sub_threads:
			t.join()
		self._sub_threads = []
		logging.debug('Waiting for GenericConnection Sub-Routines has ended')

	def disconnect(self, reconnect: bool = False):
		logging.debug('Disconnect has been invoked; Reconnedt flag: %s', reconnect)

		self._connection_shutdown(self._cib.socket, reconnect)

	def _connection_shutdown(self, s, is_auto_reconnect: bool = False):
		if self._cib.is_connected or not self._is_shutdown:
			logging.debug('Shutting down has been invoked')

			if self._inputs and s in self._inputs:
				self._inputs.remove(s)
			if self._outputs and s in self._outputs:
				self._outputs.remove(s)
			self._is_shutdown = True
			self._cib.is_connected = False

			self._trigger_event(self.EVENT_DISCONNECTED)
			# TODO  FIX IT ASAP!
			# FIX   Important!
			# if is_auto_reconnect:
			# 	self._trigger_event(self.EVENT_RECONNECT)

	@classmethod
	def prepare_client(cls, callback: callable, pem_bundle_name: str, host: str, port: int, is_ssl_disabled: bool) -> None:
		context = ssl.create_default_context()
		context.check_hostname = False
		context.verify_mode = ssl.CERT_NONE

		with socket.create_connection((host, port)) as sock:

			if is_ssl_disabled:
				print("WARNING: SSL IS DISABLED! It's a huge security violation!")
				logging.warning("WARNING: SSL IS DISABLED! It's a huge security violation!")

				cib = ConnInfoBlock.wrap_socket(sock, host, port)
				callback(cib)
			else:
				with context.wrap_socket(sock, server_hostname=host) as ssl_sock:
					cib = ConnInfoBlock.wrap_socket(ssl_sock, host, port)
					callback(cib)

	@classmethod
	def prepare_server(cls, callback: callable, pem_bundle_name: str, host: str, port: int, is_ssl_disabled: bool) -> None:

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
			sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			sock.bind((host, port))
			sock.listen(1)

			if is_ssl_disabled:
				print("WARNING: SSL IS DISABLED! It's a huge security violation!")
				logging.warning("WARNING: SSL IS DISABLED! It's a huge security violation!")
				callback(sock)
			else:
				context = Utils.get_server_socket_context(pem_bundle_name)
				with context.wrap_socket(sock, server_side=True) as ssl_sock:
					callback(ssl_sock)

	@classmethod
	def gen_new_server_connection(cls, sock, event_bindings) -> Generator:
		readable, _, exceptional = select.select([sock, ], [], [], 5)
		for s in readable:
			if isinstance(sock, SSLSocket):
				print(f'SSL Version: {sock}')
			logging.debug("Waiting for new incoming connections")
			cib = ConnInfoBlock.from_accept(s.accept())
			logging.debug("Accepting new incoming connection: %s", cib)
			connection = GenericConnection(cib, event_bindings)

			yield connection

	@classmethod
	def gen_new_client_connection(cls, cib, event_bindings) -> 'GenericConnection':
		logging.debug("Creating new outcoming connection")

		connection = GenericConnection(cib, event_bindings)

		logging.debug("New outcoming connection has been created: %s", cib)

		return connection
