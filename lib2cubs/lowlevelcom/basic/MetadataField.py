import base64
import json
from collections import OrderedDict


class MetadataField:

	_data: OrderedDict = None

	def __init__(self, data: str or bytes or dict or OrderedDict or None = None):
		if isinstance(data, bytes):
			data = self.parse(data)
		if isinstance(data, str):
			data = self.parse(data.encode('utf-8'))
		if data:
			self._data = OrderedDict(data)
		else:
			self._data = OrderedDict()

	def __getitem__(self, k: str):
		return self._data[k]

	def __delitem__(self, k: str):
		del self._data[k]

	def __setitem__(self, k: str, v: str):
		self._data[k] = v

	def __bytes__(self):
		return self.pack()

	def __str__(self):
		return self.pack().decode('utf-8')

	def items(self):
		return self._data.items()

	def values(self):
		return self._data.values()

	def keys(self):
		return self._data.keys()

	def pack(self) -> bytes:
		base_byte_str: bytes = json.dumps(self._data).encode('utf-8')
		return base64.b64encode(base_byte_str) if base_byte_str else None

	def unpack(self) -> dict:
		return dict(self._data)

	@classmethod
	def parse(cls, byte_str: bytes):
		base_str = base64.b64decode(byte_str).decode('utf-8')
		return json.loads(base_str) if byte_str else None
