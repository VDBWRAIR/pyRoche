import nose
import os
import os.path

from ..alignmentinfo import AlignmentInfo, CoverageRegion, BaseInfo, BadFormatException

import fixtures

class TestAlignmentInfo( object ):
    pass

class TestMergeRegions( TestAlignmentInfo ):
    def test_mergeregions_fixedexamples( self ):
        ''' Test fixed examples. ported from the doctests. Sorry future self for doing this '''
        ai = AlignmentInfo( os.path.join( fixtures.PATH, '05_11_2012_1_TI-MID10_PR_2357_AH3', 'mapping', '454AlignmentInfo.tsv' ) )
        merged = ai.merge_regions()
        assert merged['CY081005_NS_Boston09'] == [CoverageRegion( 1, 459, 'Gap' ), CoverageRegion( 460, 506, 'LowCoverage' )]
        assert merged['Human/1_(PB2)/H5N1/1/Thailand/2004'] == [CoverageRegion( 1, 134, 'LowCoverage' ), CoverageRegion( 135, 2106, 'Gap' ), CoverageRegion( 2107, 2134, 'LowCoverage' ), CoverageRegion( 2135, 2333, 'Normal' )]
        assert merged['CY074918_NP_Managua09'] == [CoverageRegion( 1, 1537, 'Normal' )]
        assert merged['Human/2_(PB1)/H5N1/2/Thailand/2004'] == [CoverageRegion( 1, 17, 'Gap' ), CoverageRegion( 18, 361, 'Normal' ), CoverageRegion( 362, 377, 'LowCoverage' ), CoverageRegion( 378, 1956, 'Gap' ), CoverageRegion( 1957, 2358, 'LowCoverage' )]

        ai = AlignmentInfo( os.path.join( fixtures.PATH, '08_31_2012_3_RL10_600Yu_10_VOID', 'assembly', '454AlignmentInfo.tsv' ) )
        merged = ai.merge_regions()
        merged['contig00008'] == [CoverageRegion( 1, 709, 'LowCoverage' )]
        merged['contig00006'] == [CoverageRegion( 1, 570, 'LowCoverage' ), CoverageRegion( 571, 743, 'Normal' ), CoverageRegion( 744, 773, 'LowCoverage' ), CoverageRegion( 774, 779, 'Normal' ), CoverageRegion( 780, 866, 'LowCoverage' )]

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
