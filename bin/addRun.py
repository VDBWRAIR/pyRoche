#!/usr/bin/env python

from roche.newbler.newblercommand import AddRun
import sys
import subprocess
import logging

logging.basicConfig(level=logging.DEBUG)

ar = AddRun()
try:
    ar.run( " ".join( sys.argv[1:] ) )
except subprocess.CalledProcessError as e:
    pass
