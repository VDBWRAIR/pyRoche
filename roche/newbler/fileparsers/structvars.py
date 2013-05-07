from descriptors import *

from StringIO import StringIO
from itertools import izip_longest

class RefPos( GreaterThanZeroInt ):
    ''' Allow a question mark as a valid input '''
    def __set__( self, inst, value ):
        if value == '?':
            setattr( inst, self.store_name, value )
        else:
            super( RefPos, self ).__set__( inst, value )

class DevLength( GreaterThanZeroInt ):
    ''' Allow a hyphen mark as a valid input '''
    def __set__( self, inst, value ):
        if value == '-':
            setattr( inst, self.store_name, value )
        else:
            super( DevLength, self ).__set__( inst, value )

class StructVars( object ):
    def __init__( self, fh_or_filepath ):
        ''' Init the class '''
        # Store all the variants in a list
        self._variant_list = []
        # Also key the variants by the refaccno1
        self._variant_by_ref = {}
        self.parse( fh_or_filepath )

    def parse( self, fh_or_filepath ):
        self.fh = fh_or_filepath
        if isinstance( fh_or_filepath, str ):
            self.fh = open( self.fh )
        if isinstance( self.fh, StringIO ):
            self.filepath = 'Memory'
        else:
            self.filepath = self.fh.name
        self.lines = self.all_lines()
        self.parse_header()
        self.parse_struct_variants()

    @property
    def variants( self ):
        return self._variant_list

    def __getitem__( self, refaccno ):
        return self._variant_by_ref[refaccno]

    def keys( self ):
        return self._variant_by_ref.keys()

    def parse_struct_variants( self ):
        for varlines in self.read_until_next_variant():
            sl = self.parse_summary_line( varlines[0] )
            sl['lines'] = varlines[1:]
            self._variant_list.append( StructVariant( **sl ) )
            refaccno = sl['Ref Accno1']
            if refaccno not in self._variant_by_ref:
                self._variant_by_ref[refaccno] = []
            self._variant_by_ref[refaccno].append( self._variant_list[-1] )

    def read_until_next_variant( self ):
        ''' Generator to loop through all variant sections '''
        var_lines = []
        for cur_line in self.lines:
            # Read until break is found
            if cur_line != '-----------------------------':
                var_lines.append( cur_line )
            else:
                yield var_lines
                var_lines = []

    def all_lines( self ):
        ''' Yield all non-blank lines '''
        for line in self.fh:
            line = line.rstrip( '\n' )
            if line == '':
                continue
            yield line

    def parse_header( self ):
        ''' Chomp off top two lines and parse into list of headers '''
        line1 = next( self.lines ).split( '\t' )
        line2 = next( self.lines ).split( '\t' )
        self.headers = [" ".join( hdr ).rstrip() for hdr in izip_longest( line1, line2, fillvalue='' )] + ['Var ID']

    def parse_summary_line( self, line ):
        ''' Parse a summary line(starts with >) '''
        cols = line.split( '\t' )
        clen = len( cols )
        hlen = len( self.headers )
        if clen != hlen:
            raise ValueError( "Summary line({}) does not have same amount of columns({}) as headers({}).".format( self.headers, clen, hlen ) )
        return dict( zip( self.headers, cols ) )

    def __del__( self ):
        self.fh.close()

class StructVariant( object ):
    ''' Represents an instance of a variant in the StructVariants '''
    refaccno1 = ""
    refpos1 = GreaterThanZeroInt( 'refpos1' )
    varside1 = ValidSetDescriptor( 'varside1', valid_values=('-->','<--') )
    regionname1 = ""
    refaccno2 = ""
    refpos2 = RefPos( 'refpos2' )
    varside2 = ValidSetDescriptor( 'varside2', valid_values=('-->','<--','?') )
    regionname2 = ""
    totaldepth = GreaterThanZeroInt( 'totaldepth' )
    varfreq = GreaterThanZeroFloat( 'varfreq' )
    deviationlength = DevLength( 'deviationlength' )
    type = ValidSetDescriptor( 'type', valid_values=('Point','Region') )
    fwdwvar = None
    refwvar = None
    fwdtotal = None
    revtotal = None
    varid = ""
    def __init__( self, *args, **kwargs ):
        '''
            Accepts all arguments that are headers that coorespond to a summary line as well as lines which
            should be a list of lines from the summary line down to the ------------------- line
        '''
        self.refaccno1 = kwargs['Ref Accno1']
        self.refpos1 = kwargs['Ref Pos1']
        self.varside1 = kwargs['Var Side1']
        self.regionname1 = kwargs['Region Name1']
        self.refaccno2 = kwargs['Ref Accno2']
        self.refpos2 = kwargs['Ref Pos2']
        self.varside2 = kwargs['Var Side2']
        self.regionname2 = kwargs['Region Name2']
        self.totaldepth = kwargs['Total Depth']
        self.varfreq = kwargs['Var Freq']
        self.deviationlength = kwargs['Deviation Length']
        self.type = kwargs['Type']
        self.varid = kwargs['Var ID']

        if 'fwdwvar' in kwargs:
            self.fwdwvar = kwargs['Fwd w Var']
            self.refwvar = kwargs['Ref w Var']
            self.fwdtotal = kwargs['Fwd Total']
            self.revtotal = kwargs['Rev Total']

        self.lines = kwargs['lines']
