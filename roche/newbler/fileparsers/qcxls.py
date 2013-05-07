########################################################################################################
##          Class to parse information contained in a Assembly/MappingQC.xls file
##  Author: Tyghe Vallard
##  Email: vallardt@gmail.com
##  Date: 10/17/2012
##  Purpose:
##      Class that knows how to parse information about a given QC.xls file contained in a 454 Project
##  Versions:
##      v1.0 - Initial Release
#########################################################################################################
from optparse import OptionParser
import os.path
import re

class UnkownFormatException( Exception ):
    pass

class QCXLS:
    filename = None
    contents = None
    def __init__( self, qcxls_filename = None ):
        self.filename = qcxls_filename
        self._read( )

    def _read( self ):
        fh = open( self.filename )
        self.contents = fh.read()
        fh.close()

    def _getSection6Table( self ):
        # Regex out just the section we want
        patt = '\s+Errors by Base Position.*'
        m = re.search( patt, self.contents, re.S )
        if not m:
            raise UnkownFormatException( "Not a valid QC file: %s" % self.filename )

        # Split up the section we want by lines
        lines = m.group( 0 ).split( '\n' )

        # The table to return as a list 
        table = []

        # Grab the headers
        headers = ['Base'] + lines[3].strip().split( '\t' )
        table.append( headers )

        # The very first line is not very useful so loop over starting at line 2
        # Also the last line is unwanted as it is blank
        for l in lines[4:-1]:
            #basenum,baseerr,cumbaseerr,ignore,errrate,obsqual,cumerrrate,cumquality,ignore,accno,pos,avguniqdep,avgaligndep,avgtotdep,minalndep,maxalndep,depscore,gccont = l.split( '\t' )
            table.append( l.split( '\t' ) )

        return table

    def getCrossReferenceTable( self ):
        # Grab the full table
        table = self._getSection6Table( )

        # Will contain the Cross Reference Table
        crt = [r[9:] for r in table]

        return crt

    def getHistogramTable( self ):
        table = self._getSection6Table( )

        # Will contain the histogram table
        hgt = [r[:9] for r in table]

        return hgt

class MappingQC(QCXLS):
    pass

class AssemblyQC(QCXLS):
    pass


def test():
    qc = QCXLS( 'examples/gsMappingDir/mapping/454MappingQC.xls' )
    #print qc.getCrossReferenceTable()
    print qc.getHistogramTable()

if __name__ == '__main__':
    # This is a library only. If it is run as a script then run tests
    test()
