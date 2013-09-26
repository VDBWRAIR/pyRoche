#!/usr/bin/env python

from roche.newbler.newblercommand import RunProject
import logging

logging.basicConfig(level=logging.DEBUG)
try:
    RunProject().run()
except:
    pass
