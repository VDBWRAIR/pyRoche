import nose

from ..alignmentinfo import AlignmentInfo, BaseInfo, BadFormatException

class TestAlignmentInfo( object ):
    pass

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
