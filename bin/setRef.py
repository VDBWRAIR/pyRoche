#!/usr/bin/env python

from roche.newbler.newblercommand import SetRef
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    SetRef().run()
except:
    pass
