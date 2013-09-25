#!/usr/bin/env python

from roche.newbler.newblercommand import NewAssembly
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    NewAssembly().run()
except:
    pass


