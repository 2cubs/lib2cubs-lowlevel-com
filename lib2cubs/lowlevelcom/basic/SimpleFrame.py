import json

from lib2cubs.lowlevelcom.basic.AppFrame import AppFrame
from lib2cubs.lowlevelcom.basic.EngineFoundation import EngineFoundation


class SimpleFrame(AppFrame):

	AF_TYPE = EngineFoundation.AF_TYPE_1

	@classmethod
	def content_byte(cls, content: any):
		return json.dumps(content).encode('utf-8')

	@classmethod
	def content_unbyte(cls, content: bytes):
		return json.loads(content)
