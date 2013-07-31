#!/usr/bin/env python2.7

import re

class NewblerMetrics( object ):
    def __init__( self, filepath ):
        self.filepath = filepath

    def __getattr__( self, name ):
        return self.parse_metrics( name )

    def parse_metrics( self, metricname ):
        '''
            Parses run metrics into a dictionary of key values

            @param metricname - Name of metric such as runMetric

            @return Dictionary of all the key,value \w = .*;
        '''
        with open( self.filepath ) as fh:
            m = re.search( metricname + '\n\s{0,}{(.*?)}', fh.read(), re.S )

        if not m:
            raise ValueError( "Could not find metrics {} in {}".format( metricname, self.filepath ) )
        
        return self.parse_section( m.group(0) )

    def parse_section( self, sectiontext ):
        '''
            Parses a section such as
                runMetrics
                {
                    key = value;
                }

            @param sectiontext - Section text inside of 454NewblerMetrics.txt
            @return dictionary keyed by word before = and value of text after =
                If the text after the = has a comma a tuple will be set as the value for that key
        '''
        m = re.findall( '(\w+)\s+=\s+(.*);', sectiontext )
        if not m:
            raise ValueError( "section is malformed" )

        # Turn the list of tuples into a dictionary
        ret = dict( m )
        
        # Fix the values so they are the correct types
        for k,v in ret.items():
            # Value is a list
            if ', ' in v:
                lst = v.replace( ' ', '' ).split( ',' )
                newval = []
                for x in lst:
                    newval.append( self.guess_type( x ) )
                ret[k] = tuple( newval )
            else:
                ret[k] = self.guess_type( v )

        return ret

    def guess_type( self, value ):
        '''
            Try to guess the type of value

            @param value - String value
            @returns the same value but hopefully of the correct type
        '''
        if '.' in value:
            value = float( value.replace( '%', '' ) )
        else:
            try:
                value = int( value )
            except ValueError as e:
                pass
        return value

