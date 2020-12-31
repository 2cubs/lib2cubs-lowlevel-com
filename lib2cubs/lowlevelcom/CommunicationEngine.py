import json
import socket

from lib2cubs.lowlevelcom.basic.MetadataField import MetadataField
from lib2cubs.lowlevelcom.basic.EngineFoundation import EngineFoundation


class CommunicationEngine(EngineFoundation):

	TYPE_SERVER = 'server'
	TYPE_CLIENT = 'client'
	TYPE_BOTH = 'both'

	DEFAULT_PORT = 60099

	@classmethod
	def types_list(cls):
		return cls.TYPE_SERVER, cls.TYPE_CLIENT, cls.TYPE_BOTH

	@classmethod
	def get_proper_frame_size(cls, length: int) -> int or None:
		for p, m in cls.size_byte_list().items():
			if length <= m:
				return p
		return None

	@classmethod
	def prepare_simple_frame(cls, data: dict, metadata: dict = None, af_type: int = EngineFoundation.AF_TYPE_1, force_size: int = None):
		data_bytes = json.dumps(data).encode('utf-8')

		data_bytes_len = len(data_bytes)

		final_frame_size = cls.get_proper_frame_size(data_bytes_len)

		if final_frame_size is None:
			# TODO Implement auto-chunking
			raise Exception('Not fitting frame size')

		_divmod_msg_len = divmod(data_bytes_len, 8)
		msg_len_bytes = _divmod_msg_len[0] + (1 if _divmod_msg_len[1] > 0 else 0)
		if final_frame_size:
			msg_len_bytes = int(final_frame_size) * 8

		msg_len_bytes_div = divmod(msg_len_bytes, 8)
		msg_len_of_len_bytes = msg_len_bytes_div[0] + (1 if msg_len_bytes_div[1] > 0 else 0)

		if msg_len_of_len_bytes > cls.SIZE_BYTE_15:
			raise Exception('Max frame size is reached')
		if af_type > cls.AF_TYPE_F:
			raise Exception(f'AF-type can\'t be bigger than {cls.AF_TYPE_F}')
		head_b = int(msg_len_of_len_bytes)

		head = int(f"{af_type:04b}{head_b:04b}", 2)
		head_bin = head.to_bytes(1, 'big')

		_neck_bin_str = "{msg_len:0{width}b}".format(msg_len=data_bytes_len, width=head_b * 8)
		neck = int(_neck_bin_str, 2)
		neck_bin = neck.to_bytes(head_b, 'big')

		metadata_res = bytes(MetadataField(metadata)) if metadata else b''

		app_frame = head_bin + neck_bin + metadata_res + b'\n' + data_bytes

		return app_frame

	@classmethod
	def server(cls, endpoint: str = '', port: int = DEFAULT_PORT):
		print('Starting Server')
		s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((endpoint, port))
		s.listen()
		# msg = f'Many Many different проверка thingies! Вторая проверка здесь Bebebebe :-P !'
		# msg *= 900
		# msg_len = len(msg)
		# force_frame_size_bytes = cls.get_proper_frame_size(msg_len)
		#
		# if force_frame_size_bytes is None:
			# TODO Implement auto-chunking
			# raise Exception('Not fitting frame size')
		#
		# _divmod_msg_len = divmod(msg_len, 8)
		# msg_len_bytes = _divmod_msg_len[0] + (1 if _divmod_msg_len[1] > 0 else 0)
		# if force_frame_size_bytes:
		# 	msg_len_bytes = int(force_frame_size_bytes) * 8
		#
		# msg_len_bytes_div = divmod(msg_len_bytes, 8)
		# msg_len_of_len_bytes = msg_len_bytes_div[0] + (1 if msg_len_bytes_div[1] > 0 else 0)
		#
		# if msg_len_of_len_bytes > 0xF:
		# 	raise Exception('Max frame size is reached')
		# head = bytes(1)
		# head_a = 0x0
		# head_b = int(msg_len_of_len_bytes)
		#
		# _head_bin_str = f"{head_a:04b}{head_b:04b}"
		# head = int(_head_bin_str, 2)
		# head_bin = head.to_bytes(1, 'big')
		#
		# _neck_bin_str = "{msg_len:0{width}b}".format(msg_len=msg_len, width=head_b * 8)
		# neck = int(_neck_bin_str, 2)
		# neck_bin = neck.to_bytes(head_b, 'big')
		#
		# print(msg_len_bytes)
		# print(head_bin, int.from_bytes(head_bin, 'big'), head)
		# print(neck_bin, int.from_bytes(neck_bin, 'big'), neck)
		#
		# body_bin_str = str(msg).encode('utf-8')
		# print(body_bin_str)
		# app_frame = head_bin + neck_bin + body_bin_str

		data = {
			'My action 1': 'Beb\nebebe 1',
			'My\n action 2': 'Bebe\nbebe 2',
			'My \naction 3': 'B\nebebebe 3',
		}
		metadata = {
			'hash': 'BEBEBE',
			'type': 'right',
			'gite': 'dite',
		}
		simple_frame = cls.prepare_simple_frame(data, metadata)
		# simple_frame = cls.prepare_simple_frame(data)
		cls.explain_frame(simple_frame)

		# while True:
		# 	conn, addr = s.accept()
		# 	print(f"{addr} has connected")
		# 	conn.send(b'Check connection?')
		# 	conn.close()

	@classmethod
	def explain_frame(cls, frame: bytes):
		print('## ', frame)
		first_byte = frame[0]
		af_type = int(first_byte >> 4)
		print(f'## AF-typef [ {af_type:04b} ]:\t\t', af_type)
		szofsz = int(first_byte & 0x0F)
		print(f'## Sz-of-sz [ {szofsz:04b} ]:\t\t', szofsz)
		sz = frame[1:szofsz + 1]
		print(f'## Payload size [ {sz} ]:\t', int.from_bytes(sz, 'big'))

		meta, payload = frame[szofsz + 1:].decode('utf-8').split('\n', maxsplit=1)
		if meta:
			print(f'## Meta [ {meta} ]:\t', MetadataField(meta).unpack())
		else:
			print(f'## No metadata!')
		print(f'## Payload:\t', json.loads(payload))

	@classmethod
	def client(cls, endpoint: str = '127.0.0.1', port: int = DEFAULT_PORT):
		print('Starting Client')
		s = socket.socket()
		s.connect((endpoint, port))
		msg = s.recv(1024)
		print(f'Received: {msg}')
		s.close()
