#!/usr/bin/env python

from roche.newbler.newblercommand import NewMapping
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    NewMapping().run()
except:
    pass

