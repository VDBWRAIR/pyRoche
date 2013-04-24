#!/usr/bin/env python

""" Instrument Directory Support(Directories like D_<somedate>*signalProcessing """
import sys, os, os.path, re
from datetime import datetime

class ProcessingDir( object ):
    """ Represents a full/signal Processing directory """
    def __init__( self, dirpath ):
        """
            Set path to directory
        """
        if not os.path.exists( dirpath ):
            raise IOError( "Processing directory %s does not exist" % dirpath )
        self.dirpath = os.path.abspath( dirpath )
        self.processingStartDate = self._getProcessingStartDate()
        self.processingEndDate = self._getProcessingEndDate()

    def listAllSff( self ):
        """
            Return a list of all sff files for Processing directory(Full paths)

            >>> pd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2012_11_15/D_2012_11_15_22_50_31_vnode_signalProcessing' )
            >>> filteredfiles = pd.listAllFiles( ['.*.sff'] )
            >>> assert all( [os.path.splitext( name )[1] == '.sff' for name in filteredfiles] )
        """
        return self.listAllFiles( ['.*.sff'] )

    def listAllFiles( self, filterf = [] ):
        """
            Returns a list of all the files for the Processing directory(Full paths)
            filterf is a sequence of file names to filter out. Only return those that match(Note: Match vs Search).

            >>> pd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2012_11_15/D_2012_11_15_22_50_31_vnode_signalProcessing' )
            >>> allfiles = pd.listAllFiles( )
            >>> assert len( allfiles ) > 1
            >>> filteredfiles = pd.listAllFiles( ['.*.cwf'] )
            >>> assert all( [os.path.splitext( name )[1] == '.cwf' for name in filteredfiles] )
        """
        names = []
        for root, dirs, files in os.walk( self.dirpath ):
            for name in files:
                if filterf:
                    for p in filterf:
                        m = re.match( p, name )
                        if m:
                            names.append( name )
                            break
                else:
                    names.append( name )
        return names

    def getDateFromPath( self, path ):
        """
            Assumes underscores separate the date parts as is usually the case for 454 Runs

            >>> from datetime import datetime
            >>> pd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2012_11_15/D_2012_11_15_22_50_31_vnode_signalProcessing' )
            >>> assert pd.getDateFromPath( 'D_2012_11_15_22_50_31_vnode_signalProcessing' ) == datetime( 2012, 11, 15, 22, 50, 31 )
            >>> assert pd.getDateFromPath( '2012_11_15' ) == datetime( 2012, 11, 15 )
            >>> assert pd.getDateFromPath( '2012_11_15Titanium' ) == datetime( 2012, 11, 15 )
        """
        # This is a processing directory path(aka end processing date)
        if path.startswith( 'D' ):
            datep = '(?P<year>[0-9]{4})_(?P<month>[0-9]{2})_(?P<day>[0-9]{2})_(?P<hour>[0-9]{2})_(?P<minute>[0-9]{2})_(?P<second>[0-9]{2})'
        # This is a data analysis dir path(aka start processing date)
        else:
            datep = '(?P<year>[0-9]{4})_(?P<month>[0-9]{2})_(?P<day>[0-9]{2})'

        s = re.search( datep, path )
        if not s:
            raise ValueError( "Incorrect date path given -->%s" % path )

        return datetime( *[int(i) for i in s.groups()] )

    def _getProcessingStartDate( self ):
        """
            Returns the start processing date from the directory path

            >>> os.path.basename( '/home/EIDRUdata/Data_seq454/2011_12_23/D_2011_12_24_00_58_20_vnode_signalProcessing' )
            'D_2011_12_24_00_58_20_vnode_signalProcessing'
        """
        return self.getDateFromPath( os.path.basename( self.dirpath ) )

    def _getProcessingEndDate( self ):
        """
            Returns the end processing date from the directory path

            >>> os.path.basename( os.path.dirname( '/home/EIDRUdata/Data_seq454/2011_12_23/D_2011_12_24_00_58_20_vnode_signalProcessing' ) )
            '2011_12_23'
        """
        return self.getDateFromPath( os.path.basename( os.path.dirname( self.dirpath ) ) )

    def getRunFile( self ):
        """
            Return the Titanium Run File for this processing dir

            # Should have 1 RunFileTitanium in it
            >>> spd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2012_11_15/D_2012_11_15_22_50_31_vnode_signalProcessing' )
            >>> assert len( spd.getRunFile() ) == 1

            # Should have 1 RunList in it
            >>> spd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2009_10_29/D_2009_10_29_15_41_43_FLX12070283_fullProcessing' )
            >>> assert len( spd.getRunFile() ) == 1

            # Has SampleList
            >>> spd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2010_06_30_Titanium/D_2010_06_30_15_32_19_FLX12070283_fullProcessing' )
            >>> assert len( spd.getRunFile() ) == 0

            # Has no runfile in it
            >>> spd = ProcessingDir( '/home/EIDRUdata/Data_seq454/2010_06_30_Titanium/D_2010_06_30_15_32_19_FLX12070283_fullProcessing' )
            >>> assert len( spd.getRunFile() ) == 0
        """
        return self.listAllFiles( ['.*[tT]itanium.*.txt', '.*(Run|Sample)List.*.txt$'] )

def _test():
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    sys.path.append( '../' )
    _test()
