import socket

from lib2cubs.lowlevelcom.basic.EngineFoundation import EngineFoundation


class CommunicationEngine(EngineFoundation):

	@classmethod
	def example_server(cls, endpoint: str = '', port: int = 60009):
		from lib2cubs.lowlevelcom.basic.SimpleFrame import SimpleFrame

		print('Starting Server')
		s = socket.socket()
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind((endpoint, port))
		s.listen()

		while True:
			conn, addr = s.accept()
			print(f"{addr} has connected")
			conn.send(bytes(SimpleFrame({'msg': 'Happy New Year 2021'})))
			conn.close()

	@classmethod
	def example_client(cls, endpoint: str = '127.0.0.1', port: int = 60009):
		from lib2cubs.lowlevelcom.basic.SimpleFrame import SimpleFrame

		print('Starting Client')
		s = socket.socket()
		s.connect((endpoint, port))
		data = SimpleFrame.parse(s.recv(1024)).content
		msg = data['msg']
		print(f'Received: {msg} | {data}')
		s.close()
