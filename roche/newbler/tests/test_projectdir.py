import os
import os.path
from os.path import join, basename, dirname, splitext
import multiprocessing
from glob import glob

from nose.tools import eq_, raises

from ..projectdir import ProjectDirectory, MissingProjectFile
from ..fileparsers.tests import fixtures
import fixtures

def dict_eq( d1, d2 ):
    d1keys = sorted( d1.keys() )
    d2keys = sorted( d2.keys() )
    eq_( d1keys, d2keys )
    for d1k, d2k in zip( d1keys, d2keys ):
        eq_( d1[d1k], d2[d2k] )

class RecursiveProblem( object ):
    def __init__( self, projdir ):
        self.projdir = projdir

    def run( self ):
        pd = ProjectDirectory( self.projdir )
        try:
            pd.AlignmentInfo
        except MissingProjectFile:
            pass

def recp( proj ):
    rp = RecursiveProblem( proj )
    rp.run()

class TestProjectDirectory( fixtures.FixtureProjectsBase ):
    def test_init( self ):
        for proj,fix in self.allprojs:
            a = ProjectDirectory( proj )

    @raises( ValueError )
    def test_badproj( self ):
        ProjectDirectory( 'InvalidDirectory' )

    def test_getfile( self ):
        for proj, fix in self.allprojs:
            pd = ProjectDirectory( proj )
            files = glob( join( pd.path, '*' ) ) + \
                    glob( join( pd.path, '.*' ) )
            for file in files:
                pd.get_file( file )

    def test_files( self ):
        for proj,fix in self.allprojs:
            pd = ProjectDirectory(proj)
            files = glob( join( pd.path, '*' ) ) + \
                    glob( join( pd.path, '.*' ) )
            files = {splitext(basename(f))[0]:f for f in files}
            dict_eq( files, pd.files )

    def test_getattr( self ):
        for proj, fix in self.allprojs:
            pd = ProjectDirectory( proj )
            for fp in fixtures.fileparsers:
                getattr( pd, fp )

    @raises(MissingProjectFile)
    def test_getattrmissing( self ):
        pd = ProjectDirectory( self.allprojs[0][0] )
        getattr( pd, 'missing' )

    def test_recursivelookup( self ):
        '''
            Targets the recursive __getattr__ lookup problem
            I don't know how to test it though because it has something to do
            with multiprocessing.Pool.map
            I want to punch it in the face
        '''
        pool = multiprocessing.Pool()
        ps = [p for p,f in self.allprojs]
        pool.map( recp, ps )
