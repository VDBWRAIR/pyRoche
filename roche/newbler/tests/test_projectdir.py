import unittest
import os
import os.path

import conf

from projectdir import ProjectDirectory, MissingProjectFile

class ProjectDirectoryTest( unittest.TestCase ):
    def test_init( self ):
        ''' Just test to make sure nothing goes haywire when importing project '''
        for pd in conf.all_projects:
            a = ProjectDirectory( os.path.join( conf.examples_dir, pd ) )
        self.assertRaises( ValueError, ProjectDirectory, os.path.join( conf.examples_dir, 'InvalidDir1' ) )

    def test_getfile( self ):
        pd = ProjectDirectory( os.path.join( conf.examples_dir, conf.mapping_projects[0] ) )
        for file in conf.files[:-1]:
            pd.get_file( file )

    def test_files( self ):
        filecounts = [28,20,36,22]
        for i, d in enumerate( conf.all_projects ):
            self.assertEqual( len( ProjectDirectory( os.path.join( conf.examples_dir, d ) ).files ), filecounts[i] )

    def tgetattr( self, d, parsers ):
        for fp in parsers:
            pd = ProjectDirectory( os.path.join( conf.examples_dir, d ) )
            getattr( pd, fp )

    def test_getattr( self ):
        for d in conf.mapping_projects:
            self.tgetattr( d, conf.mapping_fp )
        for d in conf.assembly_projects:
            self.tgetattr( d, conf.assembly_fp )
        pd = ProjectDirectory( os.path.join( conf.examples_dir, conf.mapping_projects[0] ) )
        self.assertRaises( MissingProjectFile, getattr, pd, 'missing' )
