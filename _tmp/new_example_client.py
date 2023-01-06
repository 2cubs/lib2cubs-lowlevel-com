#!/bin/env python
import logging

from lib2cubs.lowlevelcom import Connection
from lib2cubs.lowlevelcom.basic import AppFrame, SimpleFrame

if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)

	con = Connection(Connection.TYPE_CLIENT, 'localhost', 60009)
	con.ssl_info = False
	# con.connect()
	logging.info('Is ssl disabled: %s', con.is_ssl_disabled)
	logging.info('Is ssl provided: %s', con.is_ssl_provided)
	con.is_blocking_allowed = True
	logging.info(':: Connecting to a server on %s:%s ::', con.host, con.port)

	con.connect()
	logging.info(':: Sending data')
	con.send_frame(SimpleFrame('My message here!'))
