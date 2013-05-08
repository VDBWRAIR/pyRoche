import nose

from ..variantfileparser import VarFile, Variant, VAR_DIVIDER, HDR_DIVIDER

from StringIO import StringIO
import fnmatch
from glob import glob
import os.path

this_dir = os.path.dirname( os.path.abspath( __file__ ) )
example_files_dir = os.path.join( this_dir, 'example_files' )
var_files = glob(os.path.join( example_files_dir, '*Diffs.txt' )) + glob(os.path.join( example_files_dir, '*StructVars.txt' ))
var_files = {os.path.basename(f):f for f in var_files}

class VarFileNoParse( VarFile ):
    def parse( self, fh ):
        self.fh = fh

class VarFileSub( VarFile ):
    def parse_variants( self ):
        pass

class TestVarFile( object ):
    def setUp( self ):
        self.struct_hdr = '''Ref	Ref	Var	Region	Ref	Ref	Var	Region	Total	Var	Deviation	Type
Accno1	Pos1	Side1	Name1	Accno2	Pos2	Side2	Name2	Depth	Freq	Length'''
        self.struct_hdrs = [('Ref', 'Accno1'),
			('Ref', 'Pos1'),
			('Var', 'Side1'),
			('Region', 'Name1'),
			('Ref', 'Accno2'),
			('Ref', 'Pos2'),
			('Var', 'Side2'),
			('Region', 'Name2'),
			('Total', 'Depth'),
			('Var', 'Freq'),
			('Deviation', 'Length'),
            ('Type',''),
        ]
        self.diff_hdr = '''>Reference	Start	End	Ref	Var	Total	Var
>Accno	Pos	Pos	Nuc	Nuc	Depth	Freq'''
        self.diff_hdrs = [
            ('>Reference','>Accno'),
            ('Start','Pos'),
            ('End','Pos'),
            ('Ref','Nuc'),
            ('Var','Nuc'),
            ('Total','Depth'),
            ('Var','Freq')
        ]

    def test_yieldlinesblankfile( self ):
        fp = StringIO( '' )
        self.alllines( fp, [] )

    def test_yieldonlyvalidlines( self ):
        fp = StringIO( '''yieldme
>yieldme
!yieldme
#yieldme
{}
{}

\t
 
'''.format( VAR_DIVIDER, HDR_DIVIDER ) )
        # It will yield VAR_DIVIDERS
        self.alllines( fp, ['yieldme','>yieldme','!yieldme','#yieldme',VAR_DIVIDER] )

    def alllines( self, sio, expected ):
        vf = VarFileNoParse( sio )
        all_lines = [l for l in vf.all_lines()]
        print 'All Lines: {}'.format(all_lines)
        print 'Expected: {}'.format(expected)
        assert all_lines == expected

    def test_initvarfiles( self ):
        ''' Make sure all known var files can be inited '''
        for bn, fp in var_files.items():
            VarFileSub( fp )

    def test_summarylines( self ):
        ''' Yield all available summary lines '''
        for bn, fp in var_files.items():
            with open( fp ) as fh:
                vfs = VarFileSub( fh )
                for line in vfs.lines:
                    if line.startswith( '>' ):
                        getattr( vfs, 'parse_summary_line', line )

    def test_parseheader( self ):
        for hdrs,hdr in ((self.struct_hdrs,self.struct_hdr),(self.diff_hdrs,self.diff_hdr)):
            expect = [" ".join( x ).strip() for x in hdrs]
            inst = VarFileSub( StringIO( hdr ) )
            assert inst.headers == expect, "Headers parsed {} does not equal {}".format( inst.headers, expect )

class MockVariant( Variant ):
    test_attr1 = "Test Attr1"
    test_attr_2 = "Test Attr 2"

class TestVariant( object ):
    def setUp( self ):
        self.mv = MockVariant()

    def test_attrmap( self ):
        ''' Ensure the attribute map is working '''
        assert self.mv.attrmap( 'Attr' ) == 'attr'
        assert self.mv.attrmap( 'Attr Attr' ) == 'attr_attr' 

    def test_mapallkeys( self ):
        ''' Ensure that all keys of a dictionary get mapped '''
        myd = {
            'Attr': 'attr',
            'Attr Attr': 'attr_attr'
        }
        got = self.mv.mapkeys( myd )
        expected = dict( zip( myd.values(), myd.values() ) )
        print got
        print expected
        assert got == expected

    def test_setattributes_single( self ):
        attr_ops = ('test_attr1',)
        attr_vals = {'test_attr1':'value'}
        self.mv.set_attributes( attr_ops, attr_vals )
        print self.mv.test_attr1
        assert self.mv.test_attr1 == 'value'

    def test_setattributes_multi( self ):
        attr_ops = ('test_attr1','test_attr_2')
        attr_vals = {'test_attr1':'value', 'test_attr_2':'value'}
        self.mv.set_attributes( attr_ops, attr_vals )
        for attr, val in attr_vals.items():
            print getattr( self.mv, attr )
            assert getattr( self.mv, attr ) == 'value'

    def test_setattributes_missing( self ):
        attr_ops = ('missing',)
        attr_vals = {'missing':'value'}
        self.mv.set_attributes( attr_ops, attr_vals )
        assert self.mv.missing == 'value'
