import os
import os.path
import glob

PATH = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), 'fixtures' )


def gs_projects( path ):
    ''' Generate dictionary for mapping and assembly projects in path '''
    gsps = glob.glob( os.path.join( PATH, '*' ) )
    gsprojs = {'mapping':[],'assembly':[]}
    for gsp in gsps:
        if os.path.isdir( os.path.join( gsp, 'mapping' ) ):
            gsprojs['mapping'].append( gsp )
        else:
            gsprojs['assembly'].append( gsp )
    return gsprojs

GSPROJECTS = gs_projects( PATH )
