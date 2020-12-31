#!/bin/env python
from lib2cubs.lowlevelcom.CommunicationEngine import CommunicationEngine

print('Experimenting')
data = {
	'My action 1': 'Beb\nebebe 1',
	'My\n action 2': 'Bebe\nbebe 2',
	'My \naction 3': 'B\nebebebe 3',
}
metadata = {
	'hash': 'BEBEBE',
	'type': 'right',
	'gite': 'dite',
}
simple_frame = CommunicationEngine.prepare_simple_frame(data, metadata)
CommunicationEngine.explain_frame(simple_frame)
