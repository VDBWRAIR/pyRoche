#!/usr/bin/env python

from roche.newbler.newblercommand import AddRun
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    ar = AddRun().run()
except:
    pass
