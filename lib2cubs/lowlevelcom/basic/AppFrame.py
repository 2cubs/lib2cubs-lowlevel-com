from abc import ABCMeta
from ssl import SSLWantReadError

from lib2cubs.lowlevelcom.basic import EngineFoundation, MetadataField


class AppFrame(metaclass=ABCMeta):

	AF_TYPE = EngineFoundation.AF_TYPE_0

	_sz_of_sz: int = 0
	_size: int = 0
	_metadata: MetadataField = None
	_content: any = None

	_first_field: int = None
	_first_field_af_type: int = None
	_first_field_szofsz: int = None
	_second_field_bs: bytearray = b''
	_second_field: int = None
	_is_construction_completed: bool = False
	_payload: bytearray = b''

	@property
	def sz_of_sz(self):
		return self._sz_of_sz

	@property
	def size(self):
		return self._size

	@property
	def metadata(self):
		return self._metadata

	@metadata.setter
	def metadata(self, val):
		self._metadata = val if isinstance(val, MetadataField) or val is None else MetadataField(val)
		self._update_dependent_values()

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
			if length <= m:
				return p
		return None

	def _check_data(self):
		if self._sz_of_sz > EngineFoundation.SIZE_BYTE_15:
			raise Exception('Max frame size is reached')

	def generate(self):
		# content = json.dumps(self._content).encode('utf-8')
		content = self.content_byte(self._content)
		metadata = bytes(self._metadata) if self._metadata else b''

		head = int(f"{self.AF_TYPE:04b}{self._sz_of_sz:04b}", 2).to_bytes(1, 'big')
		neck = int("{msg_len:0{width}b}".format(msg_len=self._size, width=self._sz_of_sz * 8), 2).to_bytes(self._sz_of_sz, 'big')

		return head + neck + metadata + b'\n' + content

	def __bytes__(self):
		return self.generate()

	@classmethod
	def parse(cls, data: bytes):
		if not data:
			return False
		first_byte = data[0]
		af_type = int(first_byte >> 4)
		if cls.AF_TYPE != af_type:
			raise Exception('AF-type mismatch. Use correct class/AF-type')
		szofsz = int(first_byte & 0x0F)
		meta, content = data[szofsz + 1:].decode('utf-8').split('\n', maxsplit=1)

		return cls(cls.content_unbyte(content), MetadataField.parse(meta))

	def is_construction_completed(self):
		return self._is_construction_completed

	def from_socket(self, sock):
		if self._first_field is None:
			r = sock.recv(1)
			if not r:
				return None
			self._first_field = int.from_bytes(r, 'big')
			self._first_field_af_type = int(self._first_field >> 4)
			if self.AF_TYPE != self._first_field_af_type:
				raise Exception('AF-type mismatch. Use correct class/AF-type')
			self._first_field_szofsz = int(self._first_field & 0x0F)
		if self._first_field is not None:
			if len(self._second_field_bs) < self._first_field_szofsz:
				r = sock.recv(self._first_field_szofsz)
				if not r:
					return None
				self._second_field_bs += r
			if len(self._second_field_bs) == self._first_field_szofsz:
				self._second_field = int.from_bytes(self._second_field_bs, 'big')
			if self._second_field > 0:
				r = sock.recv(self._second_field)
				if not r:
					return None
				self._payload += r
				if len(self._payload) == self._second_field:
					meta, content = self._payload.decode('utf-8').split('\n', maxsplit=1)
					self.content = self.content_unbyte(content)
					self.metadata = MetadataField.parse(meta)
					self.clear_construct()
		return True

	def clear_construct(self):
		self._first_field = None
		self._first_field_af_type = None
		self._first_field_szofsz = None
		self._second_field_bs = b''
		self._second_field = None
		self._payload = b''
		self._is_construction_completed = True

	def __str__(self):
		return self.explain()

	def __init__(self, content: any = None, metadata: dict or MetadataField = None):
		self.content = content
		self.metadata = metadata
		if content is None:
			self._is_construction_completed = False

	def explain(self):
		s = ''
		frame = bytes(self)
		s += f'## {frame}\n'
		s += f'## AF-type [ {self.AF_TYPE:04b} ]:\t\t{self.AF_TYPE}\n'
		s += f'## Sz-of-sz [ {self._sz_of_sz:04b} ]:\t\t{self._sz_of_sz}\n'
		sz_bytes = self._size.to_bytes(self._sz_of_sz, 'big')
		s += f'## Payload size [ {sz_bytes} ]:\t{self._size}\n'
		if self._metadata:
			s += f'## Meta [ {self._metadata.pack()} ]:\t{self._metadata}\n'
		else:
			s += f'## No metadata!\n'
		s += f'## Payload:\t{self._content}\n'

		return s
