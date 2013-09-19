import os
import os.path
from os.path import join, basename, dirname, splitext
from glob import glob
import subprocess
import tempfile
import shutil

from Bio import SeqIO

FIXTURE_PATH = join( dirname( __file__ ), 'fixtures' )

# All available mapping fixtures
mapping_fixtures = glob( join( FIXTURE_PATH, 'mapping', 'fixture*' ) )
# All available assembly fixtures
assembly_fixtures = glob( join( FIXTURE_PATH, 'assembly', 'fixture*' ) )
# All available fileparsers that have been developed
pys = glob( join( '..',__file__,'fileparsers','*.py') )
fileparsers = [basename(py) for py in pys if py != '__init__.py']

class FixtureProjectsBase( object ):
    @classmethod
    def setUpClass( self ):
        self.aprojs = assemble_fixtures()
        self.mprojs = map_fixtures()
        self.allprojs = self.aprojs + self.mprojs

    @classmethod
    def tearDownClass( self ):
        # Tear down all the projects
        for proj, fixpath in self.allprojs:
            shutil.rmtree( proj )

class FixtureAssembleBase( object ): 
    @classmethod
    def setUpClass( self ):
        self.aprojs = assemble_fixtures()

    @classmethod
    def tearDownClass( self ):
        for aproj,fixturepath in self.aprojs:
            shutil.rmtree( aproj )

class FixtureMapBase( object ):
    @classmethod
    def setUpClass( self ):
        self.mprojs = map_fixtures()

    @classmethod
    def tearDownClass( self ):
        for mproj,fixturepath in self.mprojs:
            shutil.rmtree( mproj )

def map_fixtures( ):
    mprojs = []
    for fix in mapping_fixtures:
        mprojs.append( (fixture_to_project( fix ),fix) )
    return mprojs

def assemble_fixtures( ):
    aprojs = []
    for fix in assembly_fixtures:
        aprojs.append( (fixture_to_project( fix ),fix) )
    return aprojs

def files_for_fixture( fixturepath ):
    '''
        Return file sets for a fixture path
        Assumes that fixture direcotires are set up with only top level directories
            such as sff, refs and primers and that those directories do not contain
            directories in them

        @param fixturepath - Path to a fixture
        @returns dictonary keyed by directories in the fixture.
    '''
    sets = {}
    for base, dirs, files in os.walk( fixturepath ):
        if base != fixturepath:
            sets[basename(base)] = files
    return sets

def fixture_to_project( fixturepath ):
    '''
        Do mapping/assembly on a fixture
        @param fixturepath - Path to fixture
        @returns path to created project
    '''
    tdir = tempfile.mkdtemp()
    if 'mapping' in fixturepath:
        return map_fixture( fixturepath, join(tdir,'mproject') )
    else:
        return assemble_fixture( fixturepath, join(tdir,'aproject') )

def map_fixture( fixturepath, projdir ):
    ''' Run newbler mapping on fixture '''
    fixfiles = files_for_fixture( fixturepath )
    cmds = []
    cmds.append(
        ['newMapping',projdir]
    )
    cmds.append(
        ['addRun',projdir] + \
        [join(fixturepath,'sff',sff) for sff in fixfiles['sff']]
    )
    cmds.append(
        ['setRef',projdir] + \
        [join(fixturepath,'refs',ref) for ref in fixfiles['refs']]
    )
    runproj = ['runProject','-tr','-trim']
    try:
        primer = join(fixturepath,'primers',fixfiles['primers'][0])
        runproj += ['-vt',primer]
    except IndexError as e:
        pass
    runproj += [projdir]
    cmds.append(runproj)
    for cmd in cmds:
        print subprocess.check_output( cmd )

    return projdir

def assemble_fixture( fixturepath, projdir ):
    ''' Run newbler assembly on fixture '''
    fixfiles = files_for_fixture( fixturepath )
    cmds = []
    cmds.append(
        ['newAssembly',projdir]
    )
    runproj = ['runProject','-tr','-trim']
    try:
        primer = join(fixturepath,'primers',fixfiles['primers'][0])
        newproj += ['-vt',primer]
    except IndexError as e:
        pass
    runproj += [projdir]
    cmds.append(
        runproj
    )
    for cmd in cmds:
        print subprocess.check_output( cmd )

    return projdir

def refs_for_fixture( fixturepath ):
    '''
        Returns reference info for a mapping fixturepath
        @param fixturepath - Path to a fixture
        @returns dictionary of reference file basenames. Each ref key
            has identifiers in a list as the values
    '''
    fixfiles = files_for_fixture( fixturepath )
    refs = {}
    for ref in fixfiles['refs']:
        ref = join(fixturepath,'refs',ref)
        refs[basename(ref)] = [seq.id for seq in SeqIO.parse(ref,'fasta')]
    return refs
