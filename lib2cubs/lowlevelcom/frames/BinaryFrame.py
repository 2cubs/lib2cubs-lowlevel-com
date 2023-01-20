from . import AppFrame, EngineFoundation


class BinaryFrame(AppFrame):

	AF_TYPE = EngineFoundation.AF_TYPE_1

	@classmethod
	def content_byte(cls, content: any):
		return bytes(content)

	@classmethod
	def content_unbyte(cls, content: bytes):
		return content
