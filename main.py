#!/bin/env python
from argparse import ArgumentParser, Namespace

from lib2cubs.lowlevelcom import CommunicationEngine
from lib2cubs.lowlevelcom.basic import SimpleFrame


def do_explain(args: Namespace):
	data = {
		'field 1': 'value 1',
		'field 2': 'value 2',
		'field 3': 'value 3',
	}
	metadata = {
		'meta field 1': 'meta value 1',
		'meta field 2': 'meta value 2',
		'meta field 3': 'meta value 3',
	}
	frame = SimpleFrame(data, metadata)
	print(':: Explaining ::')
	print(frame.explain())


def _connection_of_type(args, sec, unsec):
	CommunicationEngine.ssl_client_key = args.client_key
	CommunicationEngine.ssl_client_cert = args.client_cert
	CommunicationEngine.ssl_server_key = args.server_key
	CommunicationEngine.ssl_server_cert = args.server_cert
	CommunicationEngine.ssl_server_hostname = args.verification_hostname

	if args.unsecure:
		if args.yes_i_totally_understand_risks:
			unsec()
		else:
			print('To proceed with --unsecure option you have to provide --yes-i-totally-understand-risks as well')
	else:
		sec()


def do_server(args: Namespace):
	print(':: Server ::')
	# For server needed both certificates, but only server key
	_connection_of_type(args, CommunicationEngine.example_secure_server, CommunicationEngine.example_server)


def do_client(args: Namespace):
	print(':: Client ::')
	# For client needed both certificates, but only client key
	_connection_of_type(args, CommunicationEngine.example_secure_client, CommunicationEngine.example_client)


def do_help(args: Namespace):
	parser.print_help()


parser = ArgumentParser()
parser.set_defaults(func=do_help)

parent = ArgumentParser(add_help=False)
parent.add_argument('--unsecure', action='store_true')
parent.add_argument('--yes-i-totally-understand-risks', action='store_true')

# To generate sample ssl keys/certs:
# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout server.key -out server.crt
# openssl req -new -newkey rsa:2048 -days 365 -nodes -x509 -keyout client.key -out client.crt
# Server generation common name (cn) should match, in the case of defaults to: 2cubs-server

parent.add_argument('--client-key', default='ssl/client.key')
parent.add_argument('--client-cert', default='ssl/client.crt')
parent.add_argument('--server-key', default='ssl/server.key')
parent.add_argument('--server-cert', default='ssl/server.crt')
parent.add_argument('--verification-hostname', default='2cubs-server')

sps = parser.add_subparsers(title='actions')
p = sps.add_parser('explain', parents=[parent])
p.set_defaults(func=do_explain)

p = sps.add_parser('server', parents=[parent])
p.set_defaults(func=do_server)

p = sps.add_parser('client', parents=[parent])
p.set_defaults(func=do_client)

args = parser.parse_args()

args.func(args)
