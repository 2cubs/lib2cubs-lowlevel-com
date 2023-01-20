#!/bin/env python3
from datetime import datetime

from lib2cubs.lowlevelcom.frames import SimpleFrame

s = SimpleFrame({
	'data': 'Some text here',
	'ts': str(datetime.now()),
})

s.explain(True)
# s.explain(True)
