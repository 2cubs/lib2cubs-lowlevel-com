#!/bin/env python
from argparse import ArgumentParser

from lib2cubs.lowlevelcom.CommunicationEngine import CommunicationEngine

parser = ArgumentParser()
parser.add_argument('side', choices=('server', 'client'))

args = parser.parse_args()
if args.side == 'server':
	CommunicationEngine.example_server()
if args.side == 'client':
	CommunicationEngine.example_client()
