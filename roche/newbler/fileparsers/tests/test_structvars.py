import nose

from StringIO import StringIO
import string

from ..structvars import StructVars, RefPos, DevLength, StructVariant

class MockRefPos( object ):
    rp = RefPos( 'rp' )
    dl = DevLength( 'dl' )

class TestRefPos( object ):
    def test_valid( self ):
        ''' Valid values '''
        mrp = MockRefPos()
        mrp.rp = '?'

    def test_invalidhyphan( self ):
        ''' Only question mark is valid non int/float value '''
        mrp = MockRefPos()
        try:
            mrp.rp = '-'
            assert False, 'Did not raise ValueError when non questionmark/float was set'
        except ValueError:
            assert True

class TestDevLength( object ):
    def test_valid( self ):
        ''' Valid values '''
        mrp = MockRefPos()
        mrp.dl = '-'

    def test_invalidhyphan( self ):
        ''' Only hyphan mark is valid non int/float value '''
        mrp = MockRefPos()
        try:
            mrp.dl = '?'
            assert False, 'Did not raise ValueError when non hyphan/int was set'
        except ValueError:
            assert True

class TestStructVars( object ):
    def setUp( self ):
        self.hdrs = [('Ref', 'Accno1'),
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
        self.shdrs = '\t'.join( [a[0] for a in self.hdrs] ) + '\n' + '\t'.join( [a[1] for a in self.hdrs] ) + '\n'
        self.actual_header	=	'''Ref	Ref	Var	Region	Ref	Ref	Var	Region	Total	Var	Deviation	Type
Accno1	Pos1	Side1	Name1	Accno2	Pos2	Side2	Name2	Depth	Freq	Length'''
        self.sio = StringIO( self.actual_header )
        self.inst = StructVars( self.sio )
        self.var = '''
>H3N2/EPI353903/Victoria361_E3E3/2011/PB2	1383	-->		?	?	?		7	28.57	-	Point	var12x
Reads with Difference:
reference                  1347+ GGG-AGTTGAA-CAC-ATCGACAGTGTGAT-GGGAATGGTTGG-A-GTATTACC-AGACATGACTCCAAGCA-CAGAGAT 1418
                                                                         *
H52E4QC02IKA2O               34+ GGGGAGTTGAA-C-CTATCGACAATGTGAT-GGGAATGATT                                        71
H52E4QC02I79BW               33+ GGGGAGTTGAA-C-CTATCGACAATGTGAT-GGGAATGATT                                        70
                                                                         *

Other Reads:
                                                                         *
H52E4QC02I5IXK              686+ GGGGAGTTGAAACAC-ATCGACAGTGTGATTGGGAATGGTTGG-A-GTATTACC-AGACATGACTCCAAGCA-CAGAGAT 760
H52E4QC02IDINK  (2)         443- GGG-AGTTGAA-CAC-ATCGACAGTGTGAT-GGGAATGGTTGG-A-GTATTACC-AGACATGACTCCAAGCA-CAGAGAT 372
H52E4QC02IM5CV  (2)         167+ GGG-AGTTGAA-CAC-ATCGACAGTGTGAT-GGGAATGGTTGG-A-GTATTACC-AGACATGACTCCAAGCA-CAGAGAT 238
H52E4QC02IF6QP              130+ GGG-AGTTGAA-CAC-ATCGACAGTGTGAT-GGGAATGGTTGG-AAGTATTACC-AGACATGACTCCAAGCA-CAGAGAT 202
H52E4QC02H1NF7               28+ GGG-AGTTGAA-C-CTATCGACAATGTGAT-GGGAATGATTGGGA--TATTGCCCAGACATGACTCCAAGCATCG-AGAT 100
                                                                         *


-----------------------------
'''

    def test_parseheader( self ):
        expect = [" ".join( x ).strip() for x in self.hdrs] + ['Var ID']
        assert self.inst.headers == expect, "Headers parsed {} does not equal {}".format( self.inst.headers, expect )

    def sumlinefactory( self, **hdrs ):
        if 'fwdwvar' in hdrs:
            fwdrev = '{Fwd w Var}\t{Rev w Var}\t{Fwd Total}\t{Rev Total}'
        else:
            fwdrev = ''
        sum_line = '{Ref Accno1}\t{Ref Pos1}\t{Var Side1}\t{Region Name1}\t{Ref Accno2}\t{Ref Pos2}\t{Var Side2}\t{Region Name2}\t{Total Depth}\t{Var Freq}\t{Deviation Length}\t{Type}{fwdrev}\t{Var ID}'
        hdrs['fwdrev'] = fwdrev
        return sum_line.format( **hdrs )

    def test_summaryparse( self ):
        refacc = '>' + string.ascii_letters + string.digits + string.punctuation
        parts = {
            'Ref Accno1': refacc,
            'Ref Pos1': '1',
            'Var Side1': '-->',
            'Region Name1': 'regname1',
            'Ref Accno2': refacc,
            'Ref Pos2': '1',
            'Var Side2': '<--',
            'Region Name2': 'regname2',
            'Total Depth': '1',
            'Var Freq': '100.0',
            'Deviation Length': '-',
            'Type': 'Point',
            'Var ID': 'var1x'
        }
        sl = self.sumlinefactory( **parts )
        sl = self.inst.parse_summary_line( sl )
        for k, v in parts.items():
            assert sl[k] == v, "Parsed summary line key {} with value {} did not match {}".format( k, sl[k], v )

    def test_struct_variants( self ):
        sio = StringIO( self.shdrs + self.var )
        sv = StructVars( sio )
        assert len( sv.variants ) == 1
        assert len( sv['>H3N2/EPI353903/Victoria361_E3E3/2011/PB2'] ) == 1

        sio = StringIO( self.shdrs + self.var + self.var )
        print sio.getvalue()
        sv = StructVars( sio )
        assert len( sv.variants ) == 2
        assert len( sv['>H3N2/EPI353903/Victoria361_E3E3/2011/PB2'] ) == 2

        sio = StringIO( self.shdrs + self.var + self.var.replace( 'PB2', 'PB1' ) )
        sv = StructVars( sio )
        assert len( sv.variants ) == 2
        assert len( sv['>H3N2/EPI353903/Victoria361_E3E3/2011/PB2'] ) == 1
        assert len( sv['>H3N2/EPI353903/Victoria361_E3E3/2011/PB1'] ) == 1

class TestStructVariant( object ):
    def test_tostring( self ):
        parts = {
            'Ref Accno1': 'testref',
            'Ref Pos1': '1',
            'Var Side1': '-->',
            'Region Name1': 'regname1',
            'Ref Accno2': '',
            'Ref Pos2': '?',
            'Var Side2': '?',
            'Region Name2': '?',
            'Total Depth': '1',
            'Var Freq': '100.0',
            'Deviation Length': '-',
            'Type': 'Point',
            'Var ID': 'var1x',
            'lines': ''
        }
        sv = StructVariant( **parts )
        print sv.__dict__
        sv.__str__()
