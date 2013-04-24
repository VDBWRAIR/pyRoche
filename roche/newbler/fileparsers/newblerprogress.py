from datetime import datetime
import re

class IncorrectDateFormat( Exception ):
    pass

class InvalidFormat(Exception):
    pass

class NewblerProgress(object):
    def __init__( self, filepath ):
        self._begindate = None
        self._enddate = None
        self.references = []
        self.trimfile = ""
        self.readfiles = []
        self.filepath = filepath
        self.succeeded = True
        self.mapping = None
        self.version = None
        self._parse()

    def _parse( self ): 
        '''
            >>> np = NewblerProgress( 'examples/08_31_2012_3_RL10_600Yu_10_VOID/assembly/454NewblerProgress.txt' )
            >>> np.references
            []
            >>> np.begindate
            datetime.datetime(2012, 9, 4, 16, 17, 19)
            >>> np.enddate
            datetime.datetime(2012, 9, 4, 16, 18, 2)
            >>> np.mapping
            False
            >>> np.readfiles
            ['08_31_2012_3_RL10_600Yu_10_VOID.sff']
            >>> np.version
            {'maj': '2.5.3', 'min': '20101207_1124'}
            >>> np = NewblerProgress( 'examples/05_11_2012_1_TI-MID10_PR_2357_AH3/mapping/454NewblerProgress.txt' )
            >>> np.references
            ['infB_Victoria.fasta', 'pdmH1N1_California.fasta', 'H3N2_Managua.fasta', 'H5N1_Thailand.fasta', 'H1N1_boston.fasta']
            >>> np.begindate
            datetime.datetime(2012, 5, 16, 15, 12, 44)
            >>> np.enddate
            datetime.datetime(2012, 5, 16, 15, 12, 56)
            >>> np.mapping
            True
            >>> np.readfiles
            ['05_11_2012_1_TI-MID10_PR_2357_AH3.sff']
            >>> np.version
            {'maj': '2.5.3', 'min': '20101207_1124'}
        '''
        with open( self.filepath ) as fh:
            for line in fh:
                line = line.strip()
                if 'Reading reference file' in line:
                    self._parse_refline( line )
                elif 'Indexing/Screening' in line:
                    self._parse_readline( line )
                elif 'computation' in line:
                    self._parse_computationline( line )
                elif 'Reading trimming database:' in line:
                    self._parse_trimdbline( line )

    def _parse_trimdbline( self, line ):
        start = len( 'Reading trimming database: ' )
        self.trimfile = line[start:]

    def _parse_readline( self, line ):
        mp = re.compile( 'Indexing/Screening(?:/Filtering){0,1}\s(?P<read>\S+?)(?:\s\(with quality scores\)){0,1}...$' )
        m = mp.match( line )
        if not m:
            raise InvalidFormat( "%s does not match %s" % (line, mp.pattern) )
        read = m.groupdict()['read']
        self.readfiles.append( read )

    def _parse_refline( self, line ):
        start = len( 'Reading reference file ' )
        self.references.append( line[start:-3] )

    @property
    def begindate( self ):
        return self._begindate
    @begindate.setter
    def begindate( self, value ):
        self._begindate = self._parse_date( value )

    @property
    def enddate( self ):
        return self._enddate
    @enddate.setter
    def enddate( self, value ):
        self._enddate = self._parse_date( value )

    def _parse_computationline( self, line ):
        '''
            Parse first or last line of file. Should be a computatoin starting or computation
            success/failure line
        '''
        mp = re.compile( '(?P<mapass>Mapping|Assembly) computation (?P<status>\w+) at: (?P<date>\w+ \w+ \d+ \d+:\d+:\d+ \d{4})(?:\s+){0,1}(?P<version>\(.*\)){0,1}$' )
        m = mp.match( line )
        if not m:
            if line.startswith( 'Error:' ):
                self.succeeded = False
                return
            else:
                raise InvalidFormat( "%s is not a valid computation line" % line )
        parsed = m.groupdict()
        if parsed['status'] == 'starting':
            self.begindate = parsed['date']
        else:
            self.enddate = parsed['date']
        self.mapping = parsed['mapass'] == 'Mapping'
        self.succeeded = parsed['status'] == 'succeeded'
        self._parse_version( parsed['version'] )
        
    def _parse_version( self, version ):
        # Only set version if it has not already been set
        if self.version is None:
            mp = re.compile( '\(v(?P<maj>[0-9\.]+)(?:\s+\((?P<min>\w+)\)){0,1}\)' )
            m = mp.match( version )
            if not m:
                raise InvalidFormat( "%s is not a valid version string. %s" % (version,mp.pattern) )
            self.version = m.groupdict()

    def _parse_date( self, dateline ):
        '''
            Parse the standard format of the date in 454NewblerProgress.txt files
        '''
        dt_format = '%a %b %d %H:%M:%S %Y'
        try:
            return datetime.strptime( dateline, dt_format )
        except ValueError as e:
            raise IncorrectDateFormat( str( e ) )

if __name__ == '__main__':
    import doctest
    doctest.testmod()
