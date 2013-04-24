###
## Parse 454MappingProject.xml
###

from Bio import SeqIO

import re
import sys
import os.path

class MappingProject:
    __file_path = None
    __file_contents = None
    def __init__( self, file_path ):
        self.__file_path = file_path
        self.__read()

    def __read( self ):
        fh = open( self.__file_path, 'r' )
        self.__file_contents = fh.read()
        fh.close()

    def abs_path( self, path ):
        if os.path.isabs( path ):
            return path
        return os.path.normpath( os.path.join( os.path.abspath( os.path.dirname( self.__file_path ) ), path ) )

    def get_primer_file( self ):
        """
            Extract and return all Primer files stored in
            VectorDatabase tag

            Tests:
                >>> a = MappingProject( 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1/mapping/454MappingProject.xml' )
                >>> b = a.get_primer_file()
                >>> print b
                /home/EIDRUdata/Tyghe/Dev/pyWrairLib/wrairlib/fff/examples/Primers/swH1N1_FD_primer_nodeg.fasta
        """
        files_pattern = "(?:<VectorDatabase/>)|(?:<VectorDatabase>(.*)</VectorDatabase>)"
        results = re.search( files_pattern, self.__file_contents, re.S )
        try:
            primerfile = results.groups()
            assert len( primerfile ) == 1
            primer = primerfile[0]
            return self.abs_path( primer )
        except AttributeError as e:
            raise ValueError( '%s does not have a VectorDatabase entry' % self.__file_path )
        except AssertionError as e:
            raise ValueError( '%s has more than one VectorDatabase entry' % self.__file_path )

    def get_reference_names( self ):
        '''
            Return a list of all reference names

            >>> a = MappingProject( 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1/mapping/454MappingProject.xml' )
            >>> b = a.get_reference_names()
            >>> len( b ) / 8 == 5
            True
        '''
        refs = []
        for reffile in self.get_reference_files():
            [refs.append( seq.id ) for seq in SeqIO.parse( reffile, 'fasta' )]
        return refs

    def get_reference_files( self ):
        """
            Extract and return all reference files

            Tests:
                >>> a = MappingProject( 'examples/05_11_2012_1_TI-MID51_PR_2305_pH1N1/mapping/454MappingProject.xml' )
                >>> b = a.get_reference_files()
                >>> type( b ) == list
                True
                >>> len( b )
                5
        """
        files_pattern = "<ReferenceFiles>.*</ReferenceFiles>"
        path_pattern = "<Path>(.*)</Path>"
        results = re.search( files_pattern, self.__file_contents, re.S )
        results = re.findall( path_pattern, results.group() )
        reffiles = []
        # Ensure all paths are absolute
        for reffile in results:
            # If the path is not absolute make it absolute
            reffiles.append( self.abs_path( reffile ) )
        return reffiles

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    if len( sys.argv ) == 2:
        if sys.argv[1] == "--test":
            _test()
