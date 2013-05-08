import nose

from ..diffs import Diffs, DiffVariant
import os
import os.path
import glob
import fnmatch

always_args = {
    'Reference Accno': 'reference_accno',
    'Start Pos': 1,
    'End Pos': 2,
    'Ref Nuc': 'A',
    'Var Nuc': 'A',
    'Total Depth': 1,
    'Var Freq': '10.0%',
    'lines': []
}
fd_args = {
    'Ref AA': '',
    'Var AA': '',
    'Coding Frame': '+',
    'Region Name': '',
    'Known SNPs': '',
    'Near SNPs': '',
    'Fwd w Var': 1,
    'Rev w Var': 1,
    'Fwd Total': 1,
    'Rev Total': 1
}
reg_args = {
    'Tgt Region Status': 'InRegion'
}

this_dir = os.path.dirname( os.path.abspath( __file__ ) )
example_files_dir = os.path.join( this_dir, 'example_files' )

class TestDiffs( object ):
    @classmethod
    def setUpClass( self ):
        self.example_files = {os.path.basename(f):f for f in glob.glob( os.path.join( example_files_dir, '*Diffs.txt' ) )}

    def setUp( self ):
        pass

    def test_initalldiffs( self ):
        Diffs( self.example_files['454AllDiffs.txt'] )

    def test_inithcdiffs( self ):
        Diffs( self.example_files['454HCDiffs.txt'] )

    def test_create_vars( self ):
        d = Diffs( self.example_files['454AllDiffs.txt'] )
        assert isinstance( d.variants[0], DiffVariant ), type( d.variants[0] )

class TestDiffVariant( object ):
    def argtest( self, args ):
        dv = DiffVariant( **args )
        for k,v in args.items():
            dvattr = getattr( dv, dv.attrmap( k ) )
            expected = v
            print 'Arg Key: ' + k
            print 'Attr: ' + dv.attrmap( k )
            print 'Expected: {}({})'.format( type(expected), expected )
            print 'Got: {}({})'.format( type(dvattr), dvattr )
            assert dvattr == expected

    def test_nofd( self ):
        self.argtest( always_args )

    def test_fd( self ):
        self.argtest( dict( fd_args, **always_args ) )

    def test_reg( self ):
        args = dict( dict( fd_args, **always_args ), **reg_args )
        self.argtest( args )
