#!/usr/bin/env python

##########################################################################
##                       454projectdir
##	Author: Tyghe Vallard						                        
##	Date: 6/5/2012							                            
##	Version: 1.0							                            
##	Description:							                            
##      Defines how to parse a Project directory path into different parts
##      
#########################################################################

import sys
import re
import os
import os.path
import pprint

from fileparsers import (refstatus, alignmentinfo, mappingproject, 
                    newblerprogress, mappingqc, allstructvars, hcstructvars,
                    alldiffs, hcdiffs, newblermetrics)

from Bio import SeqIO

class MissingProjectFile(Exception):
    pass

class ProjectDirectory( object ):
    # Set static variables
    MAPPING = 'mapping'
    ASSEMBLY = 'assembly'
    UNKNOWN = 'unkown'

    def __init__( self, dirpath = os.getcwd() ):
        # Set the base path to this project directory
        self.basepath = dirpath
        self._files = {}
        self._type = None
        if not self.isGsProjectDir( dirpath ):
            raise ValueError( "%s is not a valid Gs Project Directory" % dirpath )

    def get_file( self, name ):
        '''
            Retrieve a file path in the project by just it's name(with or without extension
        '''
        # If it has period try splitting it and searching on that name
        if '.' in name:
            try:
                return self.files[os.path.splitext( os.path.basename( name ) )[0]]
            except KeyError as e:
                pass
        # Fall back on the entire name
        try:
            return self.files[name]
        except KeyError as e:
            pass
        # Try chopping of 454
        try:
            n = name.replace( '454', '' )
            return self.files[n]
        except KeyError as e:
            pass
        try:
            n = '454' + name
            return self.files[n]
        except KeyError as e:
            msg = "Project %s does not contain the file %s" % (self.basepath, name)
            raise MissingProjectFile( msg )

    @property
    def files( self ):
        '''
            Return all the filenames under the mapping/assembly directory
        '''
        # Only retreive file list once
        if not self._files:
            # Setup the files dictionary keyed by just filename without extension
            for pfile in os.listdir( self.path ):
                filename, fileext = os.path.splitext( os.path.basename( pfile ) )
                # Index full path by just the filename without extension
                self._files[filename] = os.path.join( self.path, pfile )
        return self._files

    def __getattr__( self, name ):
        '''
            Allows dynamic retrieval of file parser objects for files within the project
        '''
        # I don't know why this needs to be here, but apparently when multiprocessing.Pool.map
        #  is called it goes into a recursive loop as if the normal class lookup mechanism
        #  is not being used. So here we force the super class's getattr to be called
        #try:
        #    return super( ProjectDirectory, self ).__getattrbute__( name )
        #except AttributeError as e:
        #    pass
        # Fetch the filepath using the attribute name that was attempted
        try:
            filepath = self.get_file( name )
            # This is scary as I'm not entirely sure how it works
            module = globals()[name.lower()]
            # Once the module is grabbed then return the instance
            return getattr( module, name )( filepath )
        except (ValueError,KeyError) as e:
            raise AttributeError( "No fileparser for %s(%s)" % (name,str(e)) )

    @property
    def path( self ):
        ''' The path to the actual mapping/assembly information '''
        return os.path.join( self.basepath, self.project_type )

    @property
    def project_type( self ):
        ''' Mapping or Assembly Project '''
        if self._type is not None:
            return self._type
        if os.path.isdir( os.path.join( self.basepath, self.MAPPING ) ):
            return self.MAPPING
        elif os.path.isdir( os.path.join( self.basepath, self.ASSEMBLY ) ):
            return self.ASSEMBLY
        else:
            return self.UNKNOWN

    def isGsProjectDir( self, path ):
        '''
            Is the path given a gsMapper or gsAssembly directory
            Aka, does it contain a 454Project.xml file and has either mapping or assembly dir
        '''
        test1 = os.path.isdir( path ) and os.path.exists( os.path.join( path, '454Project.xml' ) )
        return test1 and self.project_type != self.UNKNOWN
