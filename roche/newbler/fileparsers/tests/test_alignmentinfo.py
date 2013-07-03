import nose
from nose.tools import eq_, raises
import os
import os.path
import tempfile
import shutil

from ..alignmentinfo import AlignmentInfo, SeqAlignment, CoverageRegion as cr, BaseInfo, BadFormatException

import fixtures

aifn = '454AlignmentInfo.tsv'

class TestAlignmentInfo( object ):
   def test_parse( self ):
        for ptype, projs in fixtures.GSPROJECTS.items():
            for projpath in projs: 
                ai = AlignmentInfo( os.path.join( projpath, ptype, aifn ) ) 

class TestMergeRegions( TestAlignmentInfo ):
    def test_mergeregions_fixedexamples( self ):
        '''
            Test fixed examples. ported from the doctests.
        '''
        ai = AlignmentInfo( os.path.join( fixtures.PATH, 
            '05_11_2012_1_TI-MID10_PR_2357_AH3', 'mapping', 
            '454AlignmentInfo.tsv' ) )

        merged = ai.merge_regions()
        assert merged['CY081005_NS_Boston09'] == [
            cr( 1, 459, 'Gap' ),
            cr( 460, 506, 'LowCoverage' )
        ]
        assert merged['Human/1_(PB2)/H5N1/1/Thailand/2004'] == [
            cr( 1, 134, 'LowCoverage' ),
            cr( 135, 2106, 'Gap' ),
            cr( 2107, 2134, 'LowCoverage' ),
            cr( 2135, 2333, 'Normal' )
        ]
        assert merged['CY074918_NP_Managua09'] == [
            cr( 1, 1537, 'Normal' )
        ]
        assert merged['Human/2_(PB1)/H5N1/2/Thailand/2004'] == [
            cr( 1, 17, 'Gap' ),
            cr( 18, 361, 'Normal' ),
            cr( 362, 377, 'LowCoverage' ),
            cr( 378, 1956, 'Gap' ),
            cr( 1957, 2358, 'LowCoverage' )
        ]

        ai = AlignmentInfo( os.path.join( fixtures.PATH, 
            '08_31_2012_3_RL10_600Yu_10_VOID', 'assembly', '454AlignmentInfo.tsv' ) )
        merged = ai.merge_regions()
        merged['contig00008'] == [cr( 1, 709, 'LowCoverage' )]
        merged['contig00006'] == [cr( 1, 570, 'LowCoverage' ),
            cr( 571, 743, 'Normal' ),
            cr( 744, 773, 'LowCoverage' ),
            cr( 774, 779, 'Normal' ),
            cr( 780, 866, 'LowCoverage' )
        ]

    def test_merged_1( self ):
        ''' Specific test for R03_548__TI46__Den2 '''
        ai = AlignmentInfo( os.path.join( fixtures.PATH, 
            'R03_548__TI46__Den2', 'mapping', '454AlignmentInfo.tsv' ) )
        merged = ai.merge_regions()
        merged = merged['Den2/FJ810410_1/Thailand/2001/Den2_1']
        expected = [cr( 1, 8019, 'Normal' ),
            cr( 8020, 8021, 'LowCoverage' ),
            cr( 8022, 8068, 'Gap' ),
            cr( 8069, 8070, 'LowCoverage' ),
            cr( 8071, 9832, 'Normal' ),
            cr( 9833, 9910, 'LowCoverage' ),
            cr( 9911, 10052, 'Gap' ),
            cr( 10053, 10175, 'LowCoverage' )
        ]
        eq_( expected, merged )

    def test_merge_adjacent( self ):
        ''' Test to make sure adjacent regions of same type merge together '''
        tempdir = tempfile.mkdtemp()
        os.chdir( tempdir )
        with open( '454AlignmentInfo.tsv', 'w' ) as fh:
            fh.write( '>Region1 1\n' )
            fh.write( '1\tA\tA\t64\t1\t1\t1\t1.00\t0.01\n' )
            fh.write( '2\tA\tA\t64\t1\t1\t1\t1.00\t0.01\n' )
            fh.write( '>Region1 3\n' )
            fh.write( '3\tA\tA\t64\t1\t1\t1\t1.00\t0.01\n' )
            fh.write( '4\tA\tA\t64\t1\t1\t1\t1.00\t0.01\n' )
        ai = AlignmentInfo( '454AlignmentInfo.tsv' )
        merged = ai.merge_regions()['Region1']
        eq_( [cr(1,4,'LowCoverage'),], merged )
        os.chdir( '../' )
        shutil.rmtree( tempdir )

    def test_region_merge( self ):
        ''' Testing to make sure the transition between region types works '''
        with open( '454AlignmentInfo.tsv', 'w' ) as fh:
            fh.write( '''>Test 1
1\tG\tG\t19\t2\t11\t11\t0.81\t0.81
2\tG\tG\t19\t1\t1\t1\t0.81\t0.81
3\tC\tC\t16\t1\t1\t1\t1.08\t1.08
4\tC\tC\t16\t1\t11\t11\t1.08\t1.08
5\tC\tC\t16\t1\t11\t11\t1.08\t1.08
6\tC\tC\t16\t1\t11\t11\t1.08\t1.08
7\tC\tC\t16\t1\t11\t11\t1.08\t1.08
8\tC\tC\t16\t1\t1\t1\t1.08\t1.08
9\tC\tC\t16\t1\t1\t1\t1.08\t1.08
>Test\t13
13\tA\tA\t20\t1\t1\t1\t0.95\t0.95
14\tG\tG\t24\t1\t1\t1\t1.88\t1.88
15\tG\tG\t24\t1\t11\t11\t1.88\t1.88
16\tG\tG\t24\t1\t11\t11\t1.88\t1.88''' )
        ai = AlignmentInfo( '454AlignmentInfo.tsv' )
        eq_( [
                cr(1,1,'Normal'),
                cr(2,3,'LowCoverage'),
                cr(4,7,'Normal'),
                cr(8,9,'LowCoverage'),
            ], ai.seqs[0].regions )
        eq_( [
                cr(1,12,'Gap'),
                cr(13,14,'LowCoverage'),
                cr(15,16,'Normal'),
            ], ai.seqs[1].regions )
        merged = ai.merge_regions()['Test']
        eq_( [
                cr(1,1,'Normal'),
                cr(2,3,'LowCoverage'),
                cr(4,7,'Normal'),
                cr(8,9,'LowCoverage'),
                cr(10,12,'Gap'),
                cr(13,14,'LowCoverage'),
                cr(15,16,'Normal'),
            ],
            merged )
        os.unlink( '454AlignmentInfo.tsv' )

class TestCreateCoverageRegion( object ):
    def rgr( self, gapType ):
        ''' Random gap region '''
        import random
        start, end = (random.randint( 0, 50 ), random.randint( 50, 100 ))
        sa = SeqAlignment(['>bob 1'])
        ccr = sa.create_coverage_region( start, end, gapType )
        eq_( cr(start, end, gapType), ccr )
        
    def test_validgap( self ):
        ''' Create a valid gap region '''
        self.rgr( 'Gap' )

    def test_validnormal( self ):
        ''' Create a valid normal region '''
        self.rgr( 'Normal' )

    def test_validlowcoverage( self ):
        ''' Create a valid low coverage region '''
        self.rgr( 'LowCoverage' )

class TestSeqAlignParse( object ):
    @classmethod
    def setUpClass( self ):
        self.alignment = [
            '>Den2/FJ810410_1/Thailand/2001/Den2_1 	1',
            '1	A	A	64	4	778	778	0.92	0.12',
            '2	T	T	64	4	778	778	1.10	0.08',
            '3	G	G	64	4	778	778	0.97	0.11',
            '4	A	A	64	4	778	778	1.92	0.20',
            '5	A	A	64	4	778	778	1.92	0.20',
            '6	T	T	64	4	778	778	1.14	0.07',
            '7	A	A	64	2	232	232	3.98	0.10',
            '8	G	G	64	2	232	232	0.90	0.07',
            '9	T	T	64	2	232	232	1.95	0.17',
            '10	T	T	64	2	231	231	1.95	0.17',
            '11	C	-	64	1	2	2	0.00	0.00',
            '12	T	T	64	1	2	2	0.88	0.06',
        ]
        self.expected_regions = [cr(1,10,'Normal'), cr(11,12,'LowCoverage')]
        self.alignment2 = [
            '>Den2/FJ810410_1/Thailand/2001/Den2_1	21',
            '21	G	G	64	2	4	4	0.89	0.04',
            '22	G	-	64	2	4	4	0.89	0.04',
            '23	A	A	64	3	1299	1299	3.09	0.11',
            '24	A	A	64	3	1299	1299	3.09	0.11',
            '25	A	A	64	3	1299	1299	3.09	0.11',
        ]
        self.expected_regions2 = [cr(21,22,'LowCoverage'), cr(23,25,'Normal')]
    def test_nobeginninggap( self ):
        ''' Enusre no gap at the beginning works '''
        sa = SeqAlignment( self.alignment )
        eq_( self.expected_regions, sa.regions )

    def test_gapatbeginning( self ):
        ''' Ensure that if lastpos is not given that the gap at the beginning starts at 1 '''
        sa = SeqAlignment( self.alignment2 )
        eq_( [cr(1,20,'Gap')] + self.expected_regions2, sa.regions )
        
    def test_lastpos( self ):
        '''
            Targets a bug with seqalignment always assuming 
            gaps were from 1 to the beginning of that seqalignment
        '''
        sa = SeqAlignment( self.alignment )
        sa2 = SeqAlignment( self.alignment2, 12 )
        eq_( self.expected_regions, sa.regions )
        eq_( [cr(13,20,'Gap')] + self.expected_regions2, sa2.regions )


class TestBaseInfo( object ):
    def setUp( self ):
        self.lines = dict( 
            map_line = '1\tA\tA\t1\t1\t1\t1\t1.0\t0.01',
            assm_line = '1\tA\t1\t1\t1\t1.0\t0.01',
            badfmt_line = '1\tZ'
        )

    def test_pickmappingdenovo( self ):
        ''' Determine mapping or denovo base info '''
        bim = BaseInfo( self.lines['map_line'] )
        bia = BaseInfo( self.lines['assm_line'] )
        assert hasattr( bim, 'refb' ) and hasattr( bim, 'tdepth' )
        assert not (hasattr( bia, 'refb' ) or hasattr( bia, 'tdepth' ))
        try:
            BaseInfo( self.lines['badfmt_line'] )
            assert False
        except BadFormatException as e:
            assert True

    def test_validrefnuc( self ):
        ''' Ensure nucleotides are valid Acids '''
        # These should not throw exceptions
        BaseInfo( self.lines['map_line'] )
        BaseInfo( self.lines['assm_line'] )

        # These should
        try:
            BaseInfo( '1\tZ\t\A\t1\t1\t1\t1\t1.0\t0.01' )
            assert False, "Mapping refb base Z did not raise exception"
        except ValueError as e:
            assert True
        try:
            BaseInfo( '1\tZ\t1\t1\t1\t1.0\t0.01' )
            assert False, "Assembly consb base Z did not raise exception"
        except ValueError as e:
            assert True

    def test_posisint( self ):
        ''' Ensure pos is an integer value > 0 '''
        bi = BaseInfo( self.lines['map_line'] )
        assert isinstance( bi.pos, int )
        self.t_agtz( bi, 'pos', False )

    def t_agtz( self, inst, attr, testzero=True ):
        ''' Ensure instance attribute set to 0 and -1 raises correct error '''
        try:
            setattr( inst, attr, -1 )
            assert False, "Negative value did not raise ValueError"
        except ValueError as e:
            assert True

        if testzero:
            try:
                setattr( inst, attr, 0 )
                assert False, "Value of 0 did not raise ValueError"
            except ValueError as e:
                assert True

    def test_adepthisint( self ):
        ''' Ensure adepth is an integer >= 0 '''
        bi = BaseInfo( self.lines['map_line'] )
        assert isinstance( bi.adepth, int )
        self.t_agtz( bi, 'adepth', False )

    def test_udepthisint( self ):
        ''' Ensure adepth is an integer >= 0 '''
        bi = BaseInfo( self.lines['map_line'] )
        assert isinstance( bi.udepth, int )
        self.t_agtz( bi, 'udepth', False )

    def test_tdepthisint( self ):
        ''' Ensure adepth is an integer >= 0 '''
        bi = BaseInfo( self.lines['map_line'] )
        assert isinstance( bi.tdepth, int )
        self.t_agtz( bi, 'tdepth', False )

    def test_gaptype( self ):
        ''' Ensure gaptype is correct '''
        bi = BaseInfo( self.lines['map_line'] )
        for stype, itype in BaseInfo._gapTypes.items():
            bi.gapType = stype
            help = "GapType returned for {stype} was {gaptype}".format( stype=stype,itype=itype,gaptype=bi.gapType )
            assert bi.gapType == stype, help

    def test_tostr( self ):
        ''' Make sure correct string rep is returned '''
        bi = BaseInfo( self.lines['map_line'] )
        assert len( str( bi ).split( '\t' ) ) == 9
        bi = BaseInfo( self.lines['assm_line'] )
        assert len( str( bi ).split( '\t' ) ) == 7

class TestCoverageRegion( object ):
    def test_merge_leftequal( self ):
        ''' Left ends are equal but right ends do not. Diff rtype '''
        r = cr( 1, 5, 'Gap' ).merge( cr( 1, 3, 'Normal' ) )
        r2 = cr( 1, 5, 'Normal' ).merge( cr( 1, 3, 'Gap' ) )
        eq_( (cr( 1, 3, 'Normal'), cr( 4, 5, 'Gap' )), r )
        eq_( (cr( 1, 5, 'Normal'),), r2 )

    def test_merge_rightequal( self ):
        ''' Right ends are equal but left ends do not. Diff rtype '''
        r = cr( 1, 5, 'Gap' ).merge( cr( 3, 5, 'Normal' ) )
        r2 = cr( 1, 5, 'Normal' ).merge( cr( 3, 5, 'Gap' ) )
        eq_( (cr( 1, 2, 'Gap'), cr( 3, 5, 'Normal' )), r )
        eq_( (cr( 1, 5, 'Normal'),), r2 )

    def test_merge_backwards( self ):
        ''' Make sure that reversed regions work '''
        r = cr( 4, 6, 'Gap' ).merge( cr( 1, 3, 'Gap' ) )
        eq_( (cr( 1, 6, 'Gap' ),), r )

    def test_adjacent( self ):
        ''' Ensure adjacent same type regions are merged '''
        r = cr( 1, 3, 'Gap' ).merge( cr( 4, 5, 'Gap' ) )
        eq_( (cr( 1, 5, 'Gap' ),), r )

    def test_adjacentdiff( self ):
        ''' Ensure adjacent not same type are not modified '''
        r = cr( 1, 3, 'Gap' ).merge( cr( 4, 5, 'Normal' ) )
        eq_( (cr(1,3,'Gap' ),cr(4,5,'Normal') ), r )
        r = cr( 1, 3, 'Gap' ).merge( cr( 4, 5, 'LowCoverage' ) )
        eq_( (cr(1,3,'Gap' ),cr(4,5,'LowCoverage') ), r )

    def test_nonsameintersection( self ):
        ''' Test intersections of non sametype regions '''
        r = cr( 1, 5, 'Gap' ).merge( cr( 3, 7, 'LowCoverage' ) )
        eq_( (cr( 1, 2, 'Gap' ), 
            cr( 3, 7, 'LowCoverage' )), r )
        r = cr( 1, 5, 'Gap' ).merge( cr( 3, 7, 'Normal' ) )
        eq_((cr( 1, 2, 'Gap' ), 
            cr( 3, 7, 'Normal' )), r )
        r = cr( 1, 5, 'LowCoverage' ).merge( cr( 3, 7, 'Normal' ) )
        eq_( (cr( 1, 2, 'LowCoverage' ),
            cr( 3, 7, 'Normal' )), r )
        r = cr( 1, 5, 'LowCoverage' ).merge( cr( 3, 7, 'Gap' ) )
        eq_( (cr( 1, 5, 'LowCoverage' ),
            cr( 6, 7, 'Gap' )), r )
        r = cr( 1, 5, 'Normal' ).merge( cr( 3, 7, 'Gap' ) )
        eq_( (cr( 1, 5, 'Normal' ),
            cr( 6, 7, 'Gap' )), r )
        r = cr( 1, 5, 'Normal' ).merge( cr( 3, 7, 'LowCoverage' ) )
        eq_( (cr( 1, 5, 'Normal' ),
            cr( 6, 7, 'LowCoverage' )), r )

    def test_sametypeintersection( self ):
        r = cr( 1, 5, 'Gap' ).merge( cr( 3, 7, 'Gap' ) )
        eq_( (cr( 1, 7, 'Gap' ),), r )

    def test_regioninside( self ):
        ''' One region inside of the other and higher precedence '''
        r = cr( 1, 7, 'LowCoverage' ).merge( cr( 2, 5, 'Gap' ) )
        eq_( (cr( 1, 7, 'LowCoverage' ),), r )

    def test_split3way( self ):
        ''' Split a higher precedence by lower '''
        r = cr( 1, 7, 'Gap' ).merge( cr( 2, 5, 'LowCoverage' ) )
        eq_( (cr( 1, 1, 'Gap' ),
            cr( 2, 5, 'LowCoverage' ),
            cr( 6, 7, 'Gap' )), r )

    def test_contained( self ):
        ''' Two regions of same time, one contains other '''
        r = cr( 1, 7, 'Gap' ).merge( cr( 2, 5, 'Gap' ) )
        eq_( (cr( 1, 7, 'Gap' ),), r )

    def test_oddcases( self ):
        ''' Test rare cases '''
        r = cr( 1, 1, 'Gap' ).merge( cr( 1, 1, 'Gap' ) )
        eq_( (cr( 1, 1, 'Gap' ),), r )
        r = cr( 1, 1, 'LowCoverage' ).merge( cr( 1, 1, 'Gap' ) )
        eq_( (cr( 1, 1, 'LowCoverage' ),), r )
        r = cr( 1, 2, 'Gap' ).merge( cr( 1, 1, 'Gap' ) )
        eq_( (cr( 1, 2, 'Gap' ),), r )
        r = cr( 1, 2, 'Gap' ).merge( cr( 1, 1, 'LowCoverage' ) )
        eq_( (cr( 1, 1, 'LowCoverage' ),
            cr( 2, 2, 'Gap' )), r )

    @raises( ValueError )
    def test_notintersecting( self ):
        ''' Non intersecting cases '''
        cr( 1, 2, 'Gap' ).merge( cr( 4, 5, 'Gap' ) )

    @raises( ValueError )
    def test_nonadjacent( self ):
        ''' Non adjacent '''
        cr( 4, 5, 'Gap' ).merge( cr( 1, 2, 'Gap' ) )
