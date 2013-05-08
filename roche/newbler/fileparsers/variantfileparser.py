from StringIO import StringIO
from itertools import izip_longest
import string

VAR_DIVIDER = '-----------------------------'
HDR_DIVIDER = '______________________________'

class VarFile( object ):
    def __init__( self, fh_or_filepath ):
        ''' Init the class '''
        # Store all the variants in a list
        self._variant_list = []
        # Also key the variants by the refaccno1
        self._variant_by_name = {}
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
        self.parse_variants()

    @property
    def variants( self ):
        return self._variant_list

    def __getitem__( self, refaccno ):
        return self._variant_by_name[refaccno]

    def keys( self ):
        return self._variant_by_name.keys()

    def add_variant( self, name, variant ):
        ''' Add variant to master list and link into by_name '''
        self._variant_list.append( variant )
        if name not in self._variant_by_name:
            self._variant_by_name[name] = []
        self._variant_by_name[name].append( self._variant_list[-1] )

    def parse_variants( self ):
        raise NotImplementedError( "parse_variants needs to be implemented in subclass" )

    def read_until_next_variant( self ):
        ''' Generator to loop through all variant sections '''
        var_lines = []
        for cur_line in self.lines:
            # Read until break is found
            if cur_line != VAR_DIVIDER:
                var_lines.append( cur_line )
            else:
                yield var_lines
                var_lines = []

    def all_lines( self ):
        ''' Yield all non-blank lines '''
        for line in self.fh:
            line = line.rstrip( '\n' )
            if line in string.whitespace + HDR_DIVIDER:
                continue
            yield line

    def parse_header( self ):
        ''' Chomp off top two lines and parse into list of headers '''
        line1 = next( self.lines ).replace( ' ', '' ).split( '\t' )
        line2 = next( self.lines ).replace( ' ', '' ).split( '\t' )
        self.headers = [" ".join( hdr ).rstrip() for hdr in izip_longest( line1, line2, fillvalue='' )]

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

class Variant( object ):
    def attrmap( self, attr ):
        '''
        Attempt to map attribute names
        Try replacing space with _ and lowercase everything
        '''
        if attr in self.__dict__:
            return attr
        else:
            return attr.replace( ' ', '_' ).lower()

    def mapkeys( self, attrdict ):
        ''' Map all keys of attrdict '''
        for k in attrdict.keys():
            attrdict[self.attrmap(k)] = attrdict[k]
            del attrdict[k]
        return attrdict

    def set_attributes( self, attrs, attrvals ):
        ''' For a given set of attrs and a dict of attr:value set only the attrs in attrs '''
        for attr in attrs:
            setattr( self, attr, attrvals[attr] )
