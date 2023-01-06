from lib2cubs.lowlevelcom.basic.AppFrame import AppFrame
from lib2cubs.lowlevelcom.basic.EngineFoundation import EngineFoundation


class BinaryFrame(AppFrame):

	AF_TYPE = EngineFoundation.AF_TYPE_1

	@classmethod
	def content_byte(cls, content: any):
		return bytes(content)

	@classmethod
	def content_unbyte(cls, content: bytes):
		return content
