from unittest import TestCase
import os.path

from ..util import *
import conf

class UtilTest( TestCase ):
    def test_reffileforident( self ):
        r = os.path.join( conf.ref_dir, 'pdmH1N1_California.fasta' )
        pdir = os.path.join( conf.examples_dir, conf.mapping_projects[0] )

        rf = reference_file_for_identifier( 'california', pdir )
        self.assertEqual( r, rf )

        rf = reference_file_for_identifier( 'FJ969514_NS_California', pdir )
        self.assertEqual( r, rf )

        rf = reference_file_for_identifier( 'cantfindme', pdir )
        self.assertEqual( rf, None )
