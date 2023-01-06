#!/bin/env python
import logging

from lib2cubs.lowlevelcom.basic import AppFrame

from lib2cubs.lowlevelcom import Connection

if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)

	con = Connection(Connection.TYPE_SERVER, 'localhost', 60009)
	con.ssl_info = False
	# con.connect()
	logging.info('Is ssl disabled: %s', con.is_ssl_disabled)
	logging.info('Is ssl provided: %s', con.is_ssl_provided)
	con.is_blocking_allowed = True
	con.listen()
	logging.info(':: Waiting for clients on %s:%s ::', con.host, con.port)
	connected_client = con.accept()

	logging.info('Is client connected: %s', connected_client.is_connected)
	data = connected_client.collect_frame()
	print(data)

