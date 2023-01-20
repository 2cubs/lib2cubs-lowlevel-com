import base64
import json
from collections import OrderedDict


class MetadataField(dict):

	def __init__(self, data: str or bytes or dict or OrderedDict or None = None):
		if isinstance(data, bytes):
			self.update(self.parse(data))
		if isinstance(data, str):
			self.update(self.parse(data.encode('utf-8')))
		if isinstance(data, dict) or isinstance(data, OrderedDict):
			self.update(data)

	def __bytes__(self):
		return self.pack()

	def __str__(self):
		return self.pack().decode('utf-8')

	def pack(self) -> bytes:
		base_byte_str: bytes = json.dumps(dict(self)).encode('utf-8')
		return base64.b64encode(base_byte_str) if base_byte_str else None

	def unpack(self) -> dict:
		return dict(self)

	@classmethod
	def parse(cls, byte_str: bytes):
		base_str = base64.b64decode(byte_str).decode('utf-8')
		return cls(json.loads(base_str)) if byte_str else cls()
