import os
from distutils.core import setup

from fnmatch import fnmatch

from roche.__init__ import __version__

# Utility function to read the README file.
# Used for the long_description. It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def scripts( ):
    return [os.path.join( 'bin', f ) for f in os.listdir( 'bin' ) if not fnmatch( f, '*.swp' )]

setup(
    name = "pyRoche",
    version = __version__,
    author = "Tyghe Vallard",
    author_email = "vallardt@gmail.com",
    description = ("Python libraries for 454 Roche apps"),
    keywords = "biopython walter reed research python library roche 454 titanium",
    url = "",
    packages = [
        'roche',
        'roche.newbler',
        'roche.newbler.fileparsers',
    ],
    scripts = scripts(),
    data_files = [
    ],
    requires = [
        "numpy (>=1.6)",
        "biopython (>=1.59)",
        "configobj",
    ],
    long_description=read('README.md'),
)

