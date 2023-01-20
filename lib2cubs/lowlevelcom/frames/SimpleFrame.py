import json
from . import AppFrame, EngineFoundation


class SimpleFrame(AppFrame):

	AF_TYPE = EngineFoundation.AF_TYPE_1

	@classmethod
	def content_byte(cls, content: any):
		return json.dumps(content).encode('utf-8')

	@classmethod
	def content_unbyte(cls, content: bytes):
		return json.loads(content)

	@classmethod
	def format_content(cls, content):
		return json.dumps(content, indent=4)
