from abc import ABCMeta

from lib2cubs.lowlevelcom.CommunicationEngine import CommunicationEngine
from lib2cubs.lowlevelcom.basic.EngineFoundation import EngineFoundation
from lib2cubs.lowlevelcom.basic.MetadataField import MetadataField


class AppFrame(metaclass=ABCMeta):

	AF_TYPE = EngineFoundation.AF_TYPE_0

	_sz_of_sz: int = 0
	_size: int = 0
	_metadata: MetadataField = None
	_content: any = None

	@property
	def af_type(self):
		return self.AF_TYPE

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
		for p, m in CommunicationEngine.size_byte_list().items():
			if length <= m:
				return p
		return None

	def _check_data(self):
		if self._sz_of_sz > CommunicationEngine.SIZE_BYTE_15:
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
		first_byte = data[0]
		af_type = int(first_byte >> 4)
		if cls.AF_TYPE != af_type:
			raise Exception('AF-type mismatch. Use correct class/AF-type')
		szofsz = int(first_byte & 0x0F)
		meta, content = data[szofsz + 1:].decode('utf-8').split('\n', maxsplit=1)

		return cls(cls.content_unbyte(content), MetadataField.parse(meta))

	def __str__(self):
		return self.explain()

	def __init__(self, content: any = None, metadata: dict or MetadataField = None):
		self.content = content
		self.metadata = metadata

	# TODO refactor
	def explain(self):
		s = ''
		frame = bytes(self)
		s += f'## {frame}\n'
		first_byte = frame[0]
		af_type = int(first_byte >> 4)
		s += f'## AF-type [ {af_type:04b} ]:\t\t{af_type}\n'

		szofsz = int(first_byte & 0x0F)
		s += f'## Sz-of-sz [ {szofsz:04b} ]:\t\t{szofsz}\n'

		sz = frame[1:szofsz + 1]
		sz_int = int.from_bytes(sz, 'big')
		s += f'## Payload size [ {sz} ]:\t{sz_int}\n'

		meta, payload = frame[szofsz + 1:].decode('utf-8').split('\n', maxsplit=1)
		if meta:
			s += f'## Meta [ {meta} ]:\t{MetadataField(meta).unpack()}\n'
		else:
			s += f'## No metadata!\n'
		s += f'## Payload:\t{self.content_unbyte(payload)}\n'

		return s
