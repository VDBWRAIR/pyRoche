import sys

from descriptors import (GreaterThanZeroFloat,
    GreaterThanZeroInt,
    GreaterThanEqualZeroFloat,
    GreaterThanEqualZeroInt,
    Nucleotide)

class BadFormatException( Exception ):
    def __init__( self, error ):
        self.error = error
    def __str__( self ):
        return self.error

class AlignmentInfo(object):
    """ Parse 454AlignmentInfo.tsv """
    def __init__( self, filepath ):
        """
            >>> ai = AlignmentInfo( 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3/mapping/454AlignmentInfo.tsv' )
            >>> len( ai.seqs )
            37
            >>> ai = AlignmentInfo( 'examples/08_06_2012_1_Ti-MID30_D84_140_Dengue3/mapping/454AlignmentInfo.tsv' )
            >>> len( ai.seqs )
            2
            >>> ai = AlignmentInfo( 'examples/08_31_2012_3_RL10_600Yu_10_VOID/assembly/454AlignmentInfo.tsv' )
            >>> len( ai.seqs )
            65
        """
        self._seqs = []
        self._refs = {}
        self._parse( filepath )

    def _parse( self, filepath ):
        fh = open( filepath )
        seqalign = None
        for line in fh:
            line = line.strip()
            if line.startswith( 'Position' ):
                # Skip the header of the file
                continue
            elif line.startswith( '>' ):
                # Is beginning of a new contig in the alignment
                # If previously had data then create SeqAlignment object
                if seqalign:
                    self.add_seq( SeqAlignment( seqalign ) )
                seqalign = []
                seqalign.append( line )
            elif line[0] in "123456789":
                # Line is a base information line
                seqalign.append( line )
            else:
                raise BadFormatException( "%s has incorrect format in line %s" % (filepath, line) )
        # Indicates empty 454AlignmentInfo.tsv if seqalign is None
        if seqalign is not None:
            self.add_seq( SeqAlignment( seqalign ) )
        fh.close()

    @property
    def seqs( self ):
        return self._seqs

    def __getitem__( self, key ):
        return self._refs[key]

    def add_seq( self, seqalign ):
        self.seqs.append( seqalign )
        name = self.seqs[-1].name
        # If the identifier has already been seen
        # Keep track of which SeqAlignments are for what reference
        if name not in self._refs:
            self._refs[name] = []
        self._refs[name].append( self.seqs[-1] )

    def merge_regions( self ):
        """
            Merge all SeqAlignments with same name and return dictionary of Ref: [merged regions]
        """
        # Init the dict
        refregions = {ref: None for ref in self._refs}

        for ref, sas in self._refs.iteritems():
            regionsforref = []
            mergedregions = []
            for sa in sas:
                [regionsforref.append( region ) for region in sa.regions]

            regionsforref.sort()
            if len( regionsforref ) < 2:
                refregions[ref] = regionsforref
            else:
                # Need to ensure sorted order for merging to work
                for i in range( len( regionsforref ) - 1 ):
                    mregions = regionsforref[i].merge( regionsforref[i+1] )
                    regionsforref[i+1] = mregions[-1]
                    [mergedregions.append( region ) for region in mregions[:-1]]
                mergedregions.append( regionsforref[ len( regionsforref ) - 1 ] )

                refregions[ref] = mergedregions
            #print mergedregions
        return refregions

class SeqAlignment( object ):
    """ Represents a single sequence alignment """
    def __init__( self, seqalignment ):
        """
            >>> seqalign = []
            >>> try:
            ...   s = SeqAlignment( seqalign )
            ... except ValueError:
            ...   print "Caught"
            Caught
            >>> seqalign = [ '>SeqID1\t1' ]
            >>> s = SeqAlignment( seqalign )
            >>> seqalign = [ '>SeqID1\t1', '1\tA\tA\t1\t1\t1\t1\t1.1\t1.1' ]
            >>> s = SeqAlignment( seqalign )
            >>> s.name
            'SeqID1'
            >>> len( s.bases )
            1
            >>> print s.regions
            [CoverageRegion( 1, 1, 'LowCoverage' )]
            >>> seqalign = [\
            '>SeqID1\t1',\
            '1\tA\tA\t1\t1\t1\t1\t1.1\t1.1',\
            '2\tB\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '2\tC\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '3\tD\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '5\tE\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '8\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '9\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '10\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '11\tE\t-\t4\t1\t9\t11\t1.3\t1.3',\
            '12\tE\t-\t4\t1\t8\t11\t1.3\t1.3',\
            '14\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '14\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '15\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            '16\tE\t-\t4\t1\t11\t11\t1.3\t1.3',\
            ]
            >>> s = SeqAlignment( seqalign )
            >>> s.name
            'SeqID1'
            >>> len( s.bases )
            18
            >>> s.bases[4].pos
            4
            >>> s.bases[4].gapType
            'Gap'
            >>> len( s.regions )
            8
            >>> print s.regions[0]
            1,3,LowCoverage
            >>> print s.regions[-1]
            14,16,Normal
            >>> seqalign = [\
            '>SeqID1\t5',\
            '5\tE\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '8\tE\t-\t4\t1\t1\t1\t1.3\t1.3',\
            '9\tE\t-\t4\t1\t1\t1\t1.3\t1.3',\
            ]
            >>> s = SeqAlignment( seqalign )
            >>> len( s.bases )
            9
            >>> len( s.regions )
            4
            >>> print s.regions[0]
            1,4,Gap
        """
        if len( seqalignment ) == 0:
            raise ValueError( "No sequence alignment given" )
        self.bases = []
        # Store the bases at their actual position
        self._actual_bases = {}
        self.regions = []
        self.name, self.astart = seqalignment[0].split()
        self.name = self.name[1:]
        self.astart = int( self.astart )
        if len( seqalignment ) > 1:
            self._parse( seqalignment[1:] )

    def __getitem__( self, key ):
        return self._actual_bases[key]

    def add_base( self, base ):
        ''' Add a base to alignment '''
        self.bases.append( base )
        if self._actual_bases.get( base.pos, None ) is None:
            self._actual_bases[base.pos] = []
        self._actual_bases[base.pos].append( base )

    def _parse( self, seqalignment ):
        lastPos = self.astart - 1
        # Create coverage region for beginning
        # and add gap bases
        if lastPos != 0:
            for i in range( 1, self.astart ):
                self.add_base( BaseInfo.gapBase( i ) )
            self.regions.append( CoverageRegion( 1, lastPos, 'Gap' ) )

        # Start a new region beginning with the first base
        basei = BaseInfo( seqalignment[0] )
        self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

        for line in seqalignment:
            basei = BaseInfo( line )
            # Homopolomer or indel
            if basei.pos == lastPos:
                # Just set last pos so no gap while loop
                lastPos = basei.pos - 1
            # Insert gap bases
            if lastPos + 1 != basei.pos:
                # End old region
                self.regions[-1].end = lastPos
                # Start new gap region
                self.regions.append( CoverageRegion( lastPos + 1, lastPos + 1, 'Gap' ) )
                while lastPos + 1 != basei.pos:
                    lastPos += 1
                    self.bases.append( BaseInfo.gapBase( lastPos ) )
                # End gap region
                self.regions[-1].end = lastPos
                # Start new region
                self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

            # This base has different region type than current region
            if basei.gapType != self.regions[-1].rtype:
                self.regions[-1].end = lastPos
                self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

            self.add_base( basei )
            lastPos = basei.pos

        # end current region
        self.regions[-1].end = lastPos

class CoverageRegion( object ):
    """ Store information about a region """
    _regionTypes = { 'Gap': -1, 'LowCoverage': 0, 'Normal': 1 }
    def __init__( self, start, end, rtype = 'Normal' ):
        self.start = start
        self.end = end
        # This should be "-1 -> LC, 0 -> GAP or 1 -> BASE"
        self.rtype = rtype

    @property
    def rtypev( self ):
        """ Region type value """
        return self._regionTypes[self.rtype]

    @property
    def rtype( self ):
        return self._rtype

    @rtype.setter
    def rtype( self, value ):
        try:
            self._regionTypes[value]
            self._rtype = value
        except KeyError:
            raise ValueError( "Unknown Region Type value given: %s" % value )

    def merge( self, other ):
        """
            Merge two regions or split into 3 if needed

            # Test to make sure left & right swap
            >>> CoverageRegion( 4, 6, 'Gap' ).merge( CoverageRegion( 1, 3, 'Gap' ) )
            (CoverageRegion( 1, 3, 'Gap' ), CoverageRegion( 4, 6, 'Gap' ))

            # Ensure that non-overlapping regions are not modified
            >>> CoverageRegion( 1, 3, 'Gap' ).merge( CoverageRegion( 4, 6, 'Gap' ) )
            (CoverageRegion( 1, 3, 'Gap' ), CoverageRegion( 4, 6, 'Gap' ))

            # Test intersections of non sametype regions
            >>> CoverageRegion( 1, 5, 'Gap' ).merge( CoverageRegion( 3, 7, 'LowCoverage' ) )
            (CoverageRegion( 1, 2, 'Gap' ), CoverageRegion( 3, 7, 'LowCoverage' ))
            >>> CoverageRegion( 1, 5, 'Gap' ).merge( CoverageRegion( 3, 7, 'Normal' ) )
            (CoverageRegion( 1, 2, 'Gap' ), CoverageRegion( 3, 7, 'Normal' ))
            >>> CoverageRegion( 1, 5, 'LowCoverage' ).merge( CoverageRegion( 3, 7, 'Normal' ) )
            (CoverageRegion( 1, 2, 'LowCoverage' ), CoverageRegion( 3, 7, 'Normal' ))
            >>> CoverageRegion( 1, 5, 'LowCoverage' ).merge( CoverageRegion( 3, 7, 'Gap' ) )
            (CoverageRegion( 1, 5, 'LowCoverage' ), CoverageRegion( 6, 7, 'Gap' ))
            >>> CoverageRegion( 1, 5, 'Normal' ).merge( CoverageRegion( 3, 7, 'Gap' ) )
            (CoverageRegion( 1, 5, 'Normal' ), CoverageRegion( 6, 7, 'Gap' ))
            >>> CoverageRegion( 1, 5, 'Normal' ).merge( CoverageRegion( 3, 7, 'LowCoverage' ) )
            (CoverageRegion( 1, 5, 'Normal' ), CoverageRegion( 6, 7, 'LowCoverage' ))

            # Test intersection of sametype regions
            >>> CoverageRegion( 1, 5, 'Gap' ).merge( CoverageRegion( 3, 7, 'Gap' ) )
            (CoverageRegion( 1, 7, 'Gap' ),)


            # Test completely contained regions
            >>> CoverageRegion( 1, 7, 'LowCoverage' ).merge( CoverageRegion( 2, 5, 'Gap' ) )
            (CoverageRegion( 1, 7, 'LowCoverage' ),)

            # Test split into 3 parts
            >>> CoverageRegion( 1, 7, 'Gap' ).merge( CoverageRegion( 2, 5, 'LowCoverage' ) )
            (CoverageRegion( 1, 1, 'Gap' ), CoverageRegion( 2, 5, 'LowCoverage' ), CoverageRegion( 6, 7, 'Gap' ))

            # Test completely contained same type
            >>> CoverageRegion( 1, 7, 'Gap' ).merge( CoverageRegion( 2, 5, 'Gap' ) )
            (CoverageRegion( 1, 7, 'Gap' ),)


            # Weird cases
            >>> CoverageRegion( 1, 1, 'Gap' ).merge( CoverageRegion( 1, 1, 'Gap' ) )
            (CoverageRegion( 1, 1, 'Gap' ),)
            >>> CoverageRegion( 1, 1, 'LowCoverage' ).merge( CoverageRegion( 1, 1, 'Gap' ) )
            (CoverageRegion( 1, 1, 'LowCoverage' ),)
            >>> CoverageRegion( 1, 2, 'Gap' ).merge( CoverageRegion( 1, 1, 'Gap' ) )
            (CoverageRegion( 1, 2, 'Gap' ),)
            >>> CoverageRegion( 1, 2, 'Gap' ).merge( CoverageRegion( 1, 1, 'LowCoverage' ) )
            (CoverageRegion( 1, 1, 'LowCoverage' ), CoverageRegion( 2, 2, 'Gap' ))

            # This is a case that should just throw an exception as these regions are not
            # adjacent or intersecting
            >>> try:
            ...   CoverageRegion( 1, 2, 'Gap' ).merge( CoverageRegion( 5, 7, 'Gap' ) )
            ... except ValueError:
            ...   print "Caught"
            Caught
            >>> try:
            ...   CoverageRegion( 5, 7, 'Gap' ).merge( CoverageRegion( 1, 2, 'Gap' ) )
            ... except ValueError:
            ...   print "Caught"
            Caught
        """
        # Ensure that left is truely the left area
        left = self
        right = other
        if left > right:
            left = right
            right = self


        # Regions do not intersect
        if left.end < right.start:
            # If the regions are not adjacent throw exception
            if left.end + 1 != right.start:
                raise ValueError( "Regions do not intersect" )
            else:
                return (left, right)

        
        # Left and right regions intersect only partially(Overhang)
        # 4, 5, 6, 7
        if left.end < right.end:
            # If types are the same then merge regions
            # 6, 7
            if left.rtype == right.rtype:
                # Return new region spanning both regions
                return (CoverageRegion( left.start, right.end, left.rtype ),)
            # Need to merge the intersection portion of the regions
            # by removing that portion from the lower of the two regiontypes
            # and adding it to the other
            # 4, 5
            else:
                # Give intersection portion to right
                # 4
                if left.rtypev < right.rtypev:
                    left.end = right.start - 1
                # Give intersection portion to left
                #5
                else:
                    right.start = left.end + 1
                return (left, right)
        # Left contains right completely
        # 8, 9, 10, 11
        else:
            # If the types are the same or left has larger rtypev return
            # the bigger of the two which will be left
            # 8, 9, 10
            if left.rtypev >= right.rtypev:
                return (left,)
            # Need to split left into 2 pieces and place right in between
            # 11
            else:
                rightright = CoverageRegion( right.end + 1, left.end, left.rtype )
                left.end = right.start - 1
                return ( left, right, rightright )

    def __unicode__( self ):
        return self.__str__()

    def __str__( self ):
        return "%s,%s,%s" % (self.start, self.end, self.rtype)

    def __repr__( self ):
        return "CoverageRegion( %s, %s, '%s' )" % (self.start, self.end, self.rtype)

    def __cmp__( self, other ):
        """ self < other == -1, self == other == 0, self > other == 1 """
        if self.start == other.start \
            and self.end == other.end \
            and self.rtype == other.rtype:
            return 0
        elif self.start < other.start:
            return -1
        elif self.start > other.start:
            return 1
        elif self.start == other.start \
            and self.end <= other.end:
            return -1
        elif self.start == other.start \
            and self.end > other.end:
            return 1

class BaseInfo( object ):
    _gapTypes = {'Gap': -1, 'LowCoverage': 0, 'Normal': 1}
    pos = GreaterThanZeroInt( 'pos' )
    qual = GreaterThanEqualZeroInt( 'qual' )
    udepth = GreaterThanEqualZeroInt( 'udepth' )
    adepth = GreaterThanEqualZeroInt( 'adepth' )
    tdepth = GreaterThanEqualZeroInt( 'tdepth' )
    signal = GreaterThanEqualZeroFloat( 'signal' )
    stddev = GreaterThanEqualZeroFloat( 'stddev' )
    refb = Nucleotide( 'refb' )
    consb = Nucleotide( 'consb' )

    @staticmethod
    def gapBase( pos ):
        bi = BaseInfo( "%s\t-\t-\t64\t1\t1000\t1000\t0.0\t0.0" % pos )
        bi.gapType = 'Gap'
        return bi

    """ Represents a single base in an alignment """
    def __init__( self, seqalignline, lowcovcalc = None ):
        """
            Can feed whole line split up or just the line as a whole
        """
        if lowcovcalc is None:
            self.lcc = LowCoverageCalc

        self.parse_line( seqalignline )

        # Determine type of base
        self.gapType = 'Normal'
        if self.lcc.isLowCoverage( self ):
            self.gapType = 'LowCoverage'

    def parse_line( self, line ):
        ''' Parse tab separated line '''
        cols = line.rstrip( '\n' ).split( '\t' )
        alen = len( cols )
        if alen == 9:
            self._set_mapping( cols )
        elif alen == 7:
            self._set_assembly( cols )
        else:
            raise BadFormatException( "Incorrect amount of columns in %s" % line )

    def _set_mapping( self, mapping_cols ):
        ''' Setup mapping attributes '''
        self.pos, self.refb, self.consb, \
        self.qual, self.udepth, self.adepth, \
        self.tdepth, self.signal, self.stddev = mapping_cols

    def _set_assembly( self, assembly_cols ):
        ''' Setup assembly attributes '''
        self.pos, self.consb, \
        self.qual, self.udepth, self.adepth, \
        self.signal, self.stddev = assembly_cols

    @property
    def gapType( self ):
        return self._gapType

    @gapType.setter
    def gapType( self, value ):
        try:
            self._gapTypes[value]
            self._gapType = value
        except KeyError:
            raise ValueError( "Unknown gapType value given: %s" % value )

    def __str__( self ):
        if hasattr( self, 'refb' ):
            out = '{_pos}\t{_refb}\t{_consb}\t{_qual}\t{_udepth}\t{_adepth}\t{_tdepth}\t{_signal}\t{_stddev}'
        else:
            out = '{_pos}\t{_consb}\t{_qual}\t{_udepth}\t{_adepth}\t{_signal}\t{_stddev}'
        return out.format( **self.__dict__ )

class LowCoverageCalc( object ):
    # Less than these numbers
    lowReadThreshold = 10

    @staticmethod
    def isLowCoverage( baseinfo ):
        """
            >>> bi = BaseInfo( "1\tA\tA\t18\t18\t18\t18\t1.0\t0.01" )
            >>> print LowCoverageCalc.isLowCoverage( bi )
            False
            >>> bi = BaseInfo( "1\tA\tA\t18\t18\t1\t1\t1.0\t0.01" )
            >>> print LowCoverageCalc.isLowCoverage( bi )
            True
        """
        if LowCoverageCalc.lowReadThreshold > baseinfo.adepth:
            return True
        else:
            return False

if __name__ == '__main__':
    import doctest
    doctest.testmod()
