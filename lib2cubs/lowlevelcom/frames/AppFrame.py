import json
import logging
from abc import ABCMeta
from copy import copy
from uuid import UUID, uuid1

from . import EngineFoundation, MetadataField


class AppFrame(metaclass=ABCMeta):

	AF_TYPE = EngineFoundation.AF_TYPE_0

	_sz_of_sz: int = 0
	_size: int = 0
	_metadata: MetadataField = None
	_content: any = None

	_uid: str = None

	# _first_field: int = None
	# _first_field_af_type: int = None
	# _first_field_szofsz: int = None
	# _second_field_bs: bytearray = b''
	# _second_field: int = None
	# _is_construction_completed: bool = False
	# _payload: bytearray = b''

	@property
	def uid(self) -> UUID:
		return self._uid

	@property
	def sz_of_sz(self):
		return self._sz_of_sz

	@property
	def size(self):
		return self._size

	@property
	def metadata(self) -> MetadataField:
		return copy(self._metadata)

	def metadata_set(self, key: str, value: any):
		if key == 'uid':
			raise Exception('uid is unchangeable')

		self._metadata[key] = value
		self._update_dependent_values()

	def metadata_del(self, key: str):
		if key == 'uid':
			raise Exception('uid is unchangeable')

		del self._metadata[key]
		self._update_dependent_values()

	def metadata_get(self, key: str):
		if key in self._metadata:
			return self._metadata[key]
		return None

	#
	# @metadata.setter
	# def metadata(self, val):
	# 	self._metadata = val if isinstance(val, MetadataField) or val is None else MetadataField(val)
	# 	self._update_dependent_values()

	@property
	def content(self):
		return self._content

	@content.setter
	def content(self, val):
		self._content = val
		self._update_dependent_values()

	@classmethod
	def content_byte(cls, content: any):
		return content.encode('utf-8')

	@classmethod
	def content_unbyte(cls, content: bytes):
		return content.decode('utf-8')

	def _update_dependent_values(self):
		# data_bytes = json.dumps(self._content).encode('utf-8')
		data_bytes = self.content_byte(self._content)
		metadata_res = bytes(self._metadata) if self._metadata else b''
		self._size = len(data_bytes) + len(metadata_res) + 1
		self._sz_of_sz = self.get_proper_frame_size(self._size)
		self._check_data()

	@classmethod
	def get_proper_frame_size(cls, length: int) -> int or None:
		for p, m in EngineFoundation.size_byte_list().items():
			if length < m:
				return p
		return None

	def _check_data(self):
		if self._sz_of_sz > EngineFoundation.SIZE_BYTE_15:
			raise Exception('Max frame size is reached')

	def generate(self):
		# content = json.dumps(self._content).encode('utf-8')
		content = self.content_byte(self._content)
		if self._metadata:
			metadata = bytes(self._metadata)
		else:
			metadata = None

		head = int(f"{self.AF_TYPE:04b}{self._sz_of_sz:04b}", 2).to_bytes(1, 'big')
		try:
			neck = int("{msg_len:0{width}b}".format(msg_len=self._size, width=self._sz_of_sz * 8), 2).to_bytes(self._sz_of_sz, 'big')
			return head + neck + metadata + b'\n' + content
		except OverflowError as e:
			print('OverflowError happened')
			print(f'self._size | msg_len: {self._size}')
			print(f'self._sz_of_sz | width: {self._sz_of_sz} (* 8)')
			exit(0)

	@classmethod
	def parse(cls, data: bytes):
		if not data:
			return False
		first_byte = data[0]
		af_type = int(first_byte >> 4)
		if cls.AF_TYPE != af_type:
			raise Exception('AF-type mismatch. Use correct class/AF-type')
		szofsz = int(first_byte & 0x0F)

		_pre = data[szofsz + 1:]

		return cls(payload=_pre)

	@classmethod
	def decode_content(cls, encoded_content: str):
		return json.loads(encoded_content)

	def __init__(self, content: any = None, metadata: MetadataField = None, payload: bytes = None):
		if payload:
			try:
				meta, encoded_content = payload.decode('utf-8').split('\n', maxsplit=1)
				content = self.decode_content(encoded_content)
				metadata = MetadataField.parse(meta)
			except UnicodeDecodeError as e:
				logging.error(e)
				i = 0
				for b in payload:
					print(f"Pos {i} hex value {hex(b)} char value {chr(b)}")
					i += 1
				exit(69)

		self.content = content
		self._metadata = metadata

		if not metadata:
			self._metadata = MetadataField()

		if 'uid' not in self._metadata:
			self._metadata['uid'] = self._uid = str(uuid1())
		else:
			self._uid = self._metadata['uid']
		self._update_dependent_values()

		if content is None:
			self._is_construction_completed = False

	def explain(self, extended: bool = False, print_out: bool = True):
		res = ''
		frame = bytes(self)

		class_name = self.__class__.__name__
		uid = self.uid

		orig_type = ''
		if extended:
			orig_type = " (%s)" % hex(int(f"{self.AF_TYPE:04b}"))

		orig_szofsz = int(f"{self._sz_of_sz:04b}")
		orig_metadata = self.metadata.pack()

		if self.metadata:
			metadata = self.metadata.unpack()
		else:
			metadata = None

		content = self.format_content(self.content)

		res += f'##-##\n'
		res += f'## UID:\t\t\t\t\t {uid}\n'
		res += f'## Type:\t\t\t\t {class_name}{orig_type}\n'
		res += f'## Metadata:\t\t\t {metadata}\n'
		res += f'## Content:\t\t\t\t {content}\n'

		res += f'## Sz-of-Sz:\t\t\t {orig_szofsz}b\n'
		res += f'## Size:\t\t\t\t {self.size}b\n'
		res += f'## Content size:\t\t {len(content)}b\n'
		res += f'## Metadata size:\t\t {len(str(metadata))}b\n'

		if extended:
			res += f'##### Extended info\n'
			res += f'## Metadata enc-size:\t {len(orig_metadata)}b\n'
			res += f'## Metadata method:\t\t `base64`\n'
			res += f'## Metadata (orig):\t\t {orig_metadata}\n'
			res += f'## Frame (raw):\t\t\t {frame}\n'
		res += f'##=##\n'

		if print_out:
			print(res)
		else:
			return res

	@classmethod
	def format_content(cls, content):
		return content

	def __str__(self):
		return self.explain()

	def __bytes__(self):
		return self.generate()
