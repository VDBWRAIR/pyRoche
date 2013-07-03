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
        lastPos = 0
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
                raise BadFormatException( "%s has incorrect format in line %s" % 
                    (filepath, line) )
        # Indicates empty 454AlignmentInfo.tsv if seqalign is None
        if seqalign is not None:
            self.add_seq( SeqAlignment( seqalign ) )
        fh.close()

    @property
    def seqs( self ):
        return self._seqs

    def __getitem__( self, key ):
        return self._refs[key]

    def get_last_seq_pos( self, name ):
        '''
            Gets last position of the last gt
            @param name - name field of SeqAlignment to get last pos of
            @return Last SeqAlignment's lastPosition or 0 if no seqs have been added
        '''
        if self.seqs:
            return self.seqs[-1].lastPos
        else:
            return 0

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
            # 0 or 1 regions for ref is easy
            if len( regionsforref ) < 2:
                refregions[ref] = regionsforref
            # Merge all regions
            else:
                # Need to ensure sorted order for merging to work
                # Use a counter so we can modify the list
                for i in range( len( regionsforref ) - 1 ):
                    try:
                        # merge current and next region
                        mregions = regionsforref[i].merge( regionsforref[i+1] )
                    except ValueError as e:
                        raise ValueError( "There was an error trying to merge" + \
                            " regions for Reference {}. Error was: {}".format( ref, e ) )
                    regionsforref[i+1] = mregions[-1]
                    [mergedregions.append( region ) for region in mregions[:-1]]
                mergedregions.append( regionsforref[ len( regionsforref ) - 1 ] )

                refregions[ref] = mergedregions
        return refregions

class SeqAlignment( object ):
    """ Represents a single sequence alignment """
    def __init__( self, seqalignment, lastPos = 0 ):
        '''
            @param lastPos - Last position of the previous SeqAlignment
        '''
        if len( seqalignment ) == 0:
            raise ValueError( "No sequence alignment given" )
        self.bases = []
        # Store the bases at their actual position
        self._actual_bases = {}
        self.regions = []
        # Splits the id line on all space characters(so if they accidentally
        # put a spacetab it will cut both of them out FYI)
        self.name, self.astart = seqalignment[0].split()
        self.name = self.name[1:]
        self.astart = int( self.astart )
        self.lastPos = lastPos + 1
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

    def create_coverage_region( self, start, end, rType ):
        '''
            Create bases starting at start and ending on end(inclusive) with rtype
            
            @param start - Starting base position for coverage region(inclusive)
            @param end - Ending base position(inclusive)
            @param rtype - CoverageRegion rType
        '''
        [self.add_base( BaseInfo.static_base( i, rType ) ) \
            for i in range( start, end+1 )]
        return CoverageRegion( start, end, rType )

    def _parse( self, seqalignment ):
        # Create coverage region for beginning
        # and add gap bases
        if self.lastPos != self.astart:
            # from last position of last seqalign up to but 
            # not including the start of this seqalign
            self.regions.append( self.create_coverage_region( 
                self.lastPos, self.astart-1, 'Gap' ) )

        # Start a new region beginning with the first base
        basei = BaseInfo( seqalignment[0] )
        # Set last seen position as we are parsing the sequence lines now
        self.lastPos = basei.pos - 1
        self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

        # Loop through all the alignment lines
        for line in seqalignment:
            basei = BaseInfo( line )
            # Homopolomer or indel
            if basei.pos == self.lastPos:
                # Just set last pos so no gap while loop
                self.lastPos = basei.pos - 1
            # Insert gap bases
            if self.lastPos + 1 != basei.pos:
                # End old region
                self.regions[-1].end = self.lastPos
                # Start new gap region
                self.regions.append( CoverageRegion( self.lastPos + 1, 
                    self.lastPos + 1, 'Gap' ) )
                while self.lastPos + 1 != basei.pos:
                    self.lastPos += 1
                    self.bases.append( BaseInfo.gapBase( self.lastPos ) )
                # End gap region
                self.regions[-1].end = self.lastPos
                # Start new region
                self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

            # This base has different region type than current region
            if basei.gapType != self.regions[-1].rtype:
                self.regions[-1].end = self.lastPos
                self.regions.append( CoverageRegion( basei.pos, basei.pos, basei.gapType ) )

            self.add_base( basei )
            self.lastPos = basei.pos

        # end current region
        self.regions[-1].end = self.lastPos

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
            This method does in place editing of the regions, so be warned
            It also returns regions back so they are sorted
        """
        # Make sure that left is always a less precedence region type
        # Ensures that left.start <= right.start
        left = self
        right = other
        if left > right:
            left = right
            right = self

        # Regions do not intersect
        if left.end < right.start:
            # If the regions are not adjacent throw exception
            if left.end + 1 != right.start:
                raise ValueError( "Region {} and {} do not intersect nor are they adjacent".format( self, other ) )
            else:
                # Not the same type so return both as they were
                if left.rtype != right.rtype:
                    return (left, right)
                else:
                    # Same type so make end engulf right and return only 1 region
                    left.end = right.end
                    return (left,)

        # If the types are the same then it should be safe to just
        # merge them together
        if left.rtype == right.rtype:
            left.end = right.end
            return (left,)

        # If the regions start and end return right as we
        # ensured that right was a higher precedence above
        if left.start == right.start and left.end == right.end:
            return (right,)

        # Starts are aligned
        if left.start == right.start:
            # Left engulfs right so cut left where right ends
            if left.end > right.end:
                left.start = right.end + 1
                # Right is now smaller than left
                return (right, left)
            else:
                # Right engulfs left so just return right
                return (right,)
        # Ends are aligned(also means left.start < right.start)
        elif left.end == right.end:
            # Cut left where right starts
            if left.rtypev < right.rtypev:
                left.end = right.start - 1
                return (left, right)
            else:
                # Right is overlapped completely and less presedence so del it
                return (left,)
        # Left engulfs right completely
        elif left.end > right.end:
            # Cut left and place right in the middle
            if left.rtypev < right.rtypev:
                # Creates far right region
                leftleft = CoverageRegion( left.start, right.start - 1, left.rtype )
                # Creates far left region out of existing left
                left.start = right.end + 1
                return (leftleft, right, left)
            # right is removed as it is lower precedence
            else:
                return (left,)
        # Left and right intersect near left's end and right's start
        elif left.end < right.end:
            # Cut left.end down to right.start-1
            if left.rtypev < right.rtypev:
                left.end = right.start - 1
            else:
                # Cut right.start to left.end + 1
                right.start = left.end + 1
            return (left, right)
            

    def __unicode__( self ):
        return self.__str__()

    def __str__( self ):
        return "%s,%s,%s" % (self.start, self.end, self.rtype)

    def __repr__( self ):
        return "CoverageRegion( %s, %s, '%s' )" % (self.start, self.end, self.rtype)

    def __cmp__( self, other ):
        """ self < other == -1, self == other == 0, self > other == 1 """
        # Only equal if all pieces are equal
        if self.start == other.start \
            and self.end == other.end \
            and self.rtype == other.rtype:
            return 0
        # First compare by start values
        elif self.start < other.start:
            return -1
        elif self.start > other.start:
            return 1
        # If starts are equal compare types
        elif self.start == other.start:
            return self.rtypev.__cmp__( other.rtypev )
        #elif self.start == other.start \
        #    and self.end > other.end:
        #    return 1

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
        return BaseInfo.static_base( pos, 'Gap' )

    @staticmethod
    def static_base( pos, gapType ):
        ''' Returns a static base(usually used as a filler) '''
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
