###
## Parse 454RefStatus.txt
###

import re
import sys

class RefStatus:
    def __init__( self, file_path ):
        self.__file_path = file_path
        self.__read()

    def __read( self ):
        fh = open( self.__file_path )
        self.__file_contents = [line.strip() for line in fh.readlines()]
        fh.close()

    def _parse_headers( self ):
        '''
            Parse the top 2 lines of RefStatus

            >>> rs = RefStatus( 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1/mapping/454RefStatus.txt' )
            >>> rs._parse_headers()
            ['Reference Accession', 'Num Unique Matching Reads', 'Pct of All Unique Matches', 'Pct of All Reads', 'Pct Coverage of Reference']
            >>> rs = RefStatus( 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3/mapping/454RefStatus.txt' )
            >>> rs._parse_headers()
            ['Reference Accession', 'Num Unique Matching Reads', 'Pct of All Unique Matches', 'Pct of All Reads', 'Pct Coverage of Reference']
        '''
        h1 = self.__file_contents[0].split( '\t' )
        h2 = self.__file_contents[1].split( '\t' )
        return ["%s %s" % s for s in zip( h1, h2 )]

    def parse( self ):
        '''
            >>> rs = RefStatus( 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3/mapping/454RefStatus.txt' )
            >>> rs.parse()
            >>> stats = rs.ref_status
            >>> len( stats )
            21
            >>> next( stats.iteritems() )[1].keys()
            ['Pct of All Unique Matches', 'Pct of All Reads', 'Num Unique Matching Reads', 'Pct Coverage of Reference']
        '''
        headers = self._parse_headers( )
        self.ref_status = {}
        for line in self.__file_contents[2:]:
            s = line.split( '\t' )
            self.ref_status[s[0]] = dict( zip( headers[1:], s[1:] ) )

    def get_likely_reference( self ):
        """
            Returns the name of the most likely reference
            that was selected
            
            >>> rs = RefStatus( 'examples/gsMappingDir/mapping/454RefStatus.txt' )
            >>> rs.get_likely_reference()
            'CY074922_PB2_Managua09'
            >>> rs = RefStatus( 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1/mapping/454RefStatus.txt' )
            >>> rs.get_likely_reference()
            'FJ969514_NS_California04'
            >>> rs = RefStatus( 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3/mapping/454RefStatus.txt' )
            >>> rs.get_likely_reference()
            'CY074922_PB2_Managua09'
        """
        reflines = self.__file_contents
        if len( reflines ) > 2 and reflines[2].strip() != '':
            return reflines[2].split( '\t' )[0]
        else:
            return None

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if len( sys.argv ) == 2:
        if sys.argv[1] == "--test":
            _test()
