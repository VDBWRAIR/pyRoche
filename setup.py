import os
from distutils.core import setup

from fnmatch import fnmatch
import subprocess

# Version file to store version information in
ver_file = os.path.join( 'roche', '_version.py' )

# The major.minor version number
__version__ = 0

# Utility function to read the README file.
# Used for the long_description. It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def scripts( ):
    return [os.path.join( 'bin', f ) for f in os.listdir( 'bin' ) if not fnmatch( f, '*.swp' )]

def git_branch():
    ''' Return the current checked out branch name '''
    try:
        output = subprocess.check_output( ['git', 'branch'] ).splitlines()
    except:
        print "unable to get git branch"
        return ""

    # Get the line that the astriks is in
    branch = [x for x in output if '*' in x][0]
    branch = branch.replace( '*', '' ).strip()
    # Only return branches other than master
    if branch != 'master':
        return branch
    else:
        return ''

def set_version():
    ''' Sets the version using the current tag and revision in the git repo '''
    if not os.path.isdir(".git"):
        print "This does not appear to be a Git repository."
        return
    try:
        p = subprocess.Popen(["git", "describe", "--tags", "--always"], stdout=subprocess.PIPE)
    except EnvironmentError:
        print "unable to run git"
        return
    stdout = p.communicate()[0]
    if p.returncode != 0:
        print "unable to run git"
        return

    # Full version string
    ver = stdout.strip()
    branch = git_branch()
    if branch:
        ver += '.' + git_branch()

    with open( ver_file, 'w' ) as fh:
        global __version__
        __version__ = ver
        fh.write( "__version__ = '%s'\n" % __version__ )

    return True

# Setup
if set_version() is None:
    sys.exit( -1 )

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

